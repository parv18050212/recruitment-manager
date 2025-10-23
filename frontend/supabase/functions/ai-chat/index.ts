import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
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
    const { message, context } = await req.json();
    
    const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');
    
    // If no API key is set, return a mock response for development
    if (!GEMINI_API_KEY) {
      console.log('GEMINI_API_KEY not set, returning mock response');
      const mockResponses = {
        'candidate_assistance': {
          'How can I improve my resume for tech jobs?': `Here are some key tips to improve your tech resume:

1. **Use Action Verbs**: Start bullet points with strong action verbs like "Developed", "Implemented", "Optimized"

2. **Quantify Achievements**: Include specific numbers and metrics (e.g., "Improved performance by 40%", "Reduced load time by 2 seconds")

3. **Highlight Technical Skills**: List relevant programming languages, frameworks, and tools prominently

4. **Show Impact**: Focus on what you accomplished, not just what you did

5. **Tailor for Each Job**: Customize your resume for each position you apply to

6. **Keep it Concise**: Aim for 1-2 pages maximum

Would you like me to elaborate on any of these points?`,
          'What are the best interview preparation strategies?': `Great question! Here are proven interview preparation strategies:

1. **Research the Company**: Understand their mission, values, recent news, and company culture

2. **Practice Common Questions**: Prepare STAR method answers for behavioral questions (Situation, Task, Action, Result)

3. **Technical Preparation**: Review relevant coding concepts, practice coding problems, and understand the tech stack

4. **Prepare Questions**: Have 3-5 thoughtful questions ready to ask the interviewer

5. **Mock Interviews**: Practice with friends, family, or online platforms

6. **Dress Appropriately**: Research the company culture to determine appropriate attire

7. **Arrive Early**: Plan to arrive 10-15 minutes early

What type of interview are you preparing for?`,
          'What skills should I learn to advance my career?': `Based on current tech trends, here are high-impact skills to consider:

**Technical Skills:**
- Cloud platforms (AWS, Azure, GCP)
- Containerization (Docker, Kubernetes)
- DevOps practices
- Data analysis and visualization
- AI/ML fundamentals

**Soft Skills:**
- Communication and presentation
- Leadership and team management
- Problem-solving and critical thinking
- Adaptability and continuous learning

**Industry-Specific:**
- Cybersecurity awareness
- API development and integration
- Mobile development
- Database management

What's your current skill set and career goals? I can provide more targeted recommendations.`
        }
      };

      const contextResponses = mockResponses[context as keyof typeof mockResponses];
      const response = contextResponses?.[message as keyof typeof contextResponses] || 
        `Thanks for your question! I'm your AI Career Assistant and I'm here to help you with:

🎯 **Resume Optimization**: Tips to make your resume stand out
📝 **Interview Preparation**: Strategies to ace your interviews  
🚀 **Skill Development**: Recommendations for career advancement
💼 **Career Guidance**: Personalized advice for your career path
📊 **Industry Insights**: Current trends and market information

Feel free to ask me anything about your job search or career development. What would you like to know more about?`;

      return new Response(JSON.stringify({ response }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    console.log('Processing AI chat request:', { message, context });

    // Prepare system prompt based on context
    let systemPrompt = `You are an intelligent recruitment assistant for TalentMatch. You help with:
- Creating job descriptions from natural language
- Finding and matching candidates
- Analyzing recruitment needs
- Providing hiring insights
- Answering questions about the platform

Be conversational, helpful, and professional. Always respond in a way that moves the recruitment process forward.`;

    if (context === 'job_creation' || context === 'recruiter_assistance') {
      systemPrompt += '\n\nYou are currently helping create a job posting. Extract key details like role, skills, experience, salary, location, and company culture from the user\'s description.';
    } else if (context === 'candidate_search') {
      systemPrompt += '\n\nYou are helping search for candidates. Understand the requirements and suggest search criteria.';
    } else if (context === 'candidate_assistance') {
      systemPrompt += '\n\nYou are a Career Assistant helping job seekers with:
- Resume optimization and feedback
- Job search strategies
- Career advice and guidance
- Interview preparation tips
- Skills development recommendations
- Industry insights and trends
- Salary negotiation advice

Provide personalized, actionable advice to help candidates advance their careers. Be encouraging and supportive while giving practical guidance.';
    }

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
                text: `${systemPrompt}\n\nUser: ${message}`
              }
            ]
          }
        ],
        generationConfig: {
          temperature: 0.7,
          topK: 40,
          topP: 0.95,
          maxOutputTokens: 1024,
        }
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Gemini API error:', errorData);
      throw new Error(`Gemini API error: ${response.status}`);
    }

    const data = await response.json();
    console.log('Gemini response received');

    const aiResponse = data.candidates?.[0]?.content?.parts?.[0]?.text || 'I apologize, but I couldn\'t generate a response. Please try again.';

    return new Response(JSON.stringify({ response: aiResponse }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in ai-chat function:', error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});