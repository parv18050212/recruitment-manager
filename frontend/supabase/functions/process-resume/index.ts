import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import "https://deno.land/x/xhr@0.1.0/mod.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { resumeText, candidateId } = await req.json();
    
    const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!GEMINI_API_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
      throw new Error('Required environment variables are not set');
    }

    console.log('Processing resume for candidate:', candidateId);

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // Prepare AI prompt for resume analysis
    const systemPrompt = `You are an expert resume analyzer for a recruitment platform. Analyze the provided resume text and extract the following information in JSON format:

{
  "skills": ["skill1", "skill2", ...],
  "experience_years": number,
  "education": ["degree/certification1", "degree/certification2", ...],
  "previous_roles": ["role1", "role2", ...],
  "industries": ["industry1", "industry2", ...],
  "summary": "Brief professional summary",
  "key_achievements": ["achievement1", "achievement2", ...],
  "recommendations": {
    "missing_skills": ["skill1", "skill2", ...],
    "career_progression": "suggested next steps",
    "resume_improvements": ["improvement1", "improvement2", ...]
  }
}

Be thorough but concise. Extract only factual information from the resume.`;

    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              {
                text: `${systemPrompt}\n\nResume Text:\n${resumeText}`
              }
            ]
          }
        ],
        generationConfig: {
          temperature: 0.3,
          topK: 20,
          topP: 0.8,
          maxOutputTokens: 2048,
        }
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Gemini API error:', errorData);
      throw new Error(`Gemini API error: ${response.status}`);
    }

    const data = await response.json();
    const aiResponse = data.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!aiResponse) {
      throw new Error('No response from Gemini API');
    }

    console.log('AI analysis completed');

    // Parse the JSON response
    let analysisData;
    try {
      // Extract JSON from the response (in case there's additional text)
      const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
      const jsonString = jsonMatch ? jsonMatch[0] : aiResponse;
      analysisData = JSON.parse(jsonString);
    } catch (parseError) {
      console.error('Failed to parse AI response as JSON:', parseError);
      // Fallback: create a basic structure with the raw response
      analysisData = {
        skills: [],
        experience_years: 0,
        education: [],
        previous_roles: [],
        industries: [],
        summary: aiResponse.substring(0, 500),
        key_achievements: [],
        recommendations: {
          missing_skills: [],
          career_progression: "Unable to analyze",
          resume_improvements: []
        }
      };
    }

    // Update candidate profile with AI analysis
    const { error: updateError } = await supabase
      .from('candidates')
      .update({
        skills: analysisData.skills,
        experience_years: analysisData.experience_years,
        education: analysisData.education,
        summary: analysisData.summary,
        ai_analysis: analysisData,
        updated_at: new Date().toISOString()
      })
      .eq('id', candidateId);

    if (updateError) {
      console.error('Database update error:', updateError);
      throw new Error('Failed to update candidate profile');
    }

    console.log('Candidate profile updated successfully');

    return new Response(JSON.stringify({ 
      success: true, 
      analysis: analysisData 
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in process-resume function:', error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});