import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { Upload, FileText, Briefcase, TrendingUp, Eye, MessageSquare, Brain, Lightbulb, Target, Zap, CheckCircle2 } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import { AIChat } from '@/components/ai/AIChat';
// import { ResumeUpload } from '@/components/ai/ResumeUpload';

const CandidateDashboard = () => {
  const { toast } = useToast();
  const [stats, setStats] = useState({
    totalResumes: 0,
    jobMatches: 0,
    profileViews: 0,
    skillsExtracted: 0
  });
  const [recentMatches, setRecentMatches] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiInsights, setAiInsights] = useState({
    strengths: [],
    improvements: [],
    marketTrends: [],
    recommendations: []
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [quickPrompt, setQuickPrompt] = useState('');

  useEffect(() => {
    // Mock data load for public demo
    const timer = setTimeout(() => {
      const mockResumes = [
        {
          id: 'demo-resume-1',
          filename: 'resume_jane_doe.pdf',
          created_at: new Date().toISOString(),
          parsing_status: 'completed',
        }
      ];

      const mockMatches = [
        {
          id: 'match-1',
          fit_score: 0.86,
          skill_match_count: 7,
          total_required_skills: 9,
          jobs: { title: 'Frontend Developer', companies: { name: 'Acme Corp' } },
        },
        {
          id: 'match-2',
          fit_score: 0.78,
          skill_match_count: 6,
          total_required_skills: 9,
          jobs: { title: 'Full-Stack Engineer', companies: { name: 'Globex' } },
        }
      ];

      setStats({
        totalResumes: mockResumes.length,
        jobMatches: mockMatches.length,
        profileViews: 12,
        skillsExtracted: 24,
      });
      setRecentMatches(mockMatches as any);
      setResumes(mockResumes as any);
      setLoading(false);
    }, 400);
    return () => clearTimeout(timer);
  }, []);

  const runAIAnalysis = async () => {
    if (resumes.length === 0) {
      toast({
        title: 'No Resume Found',
        description: 'Please upload a resume first to get AI insights',
        variant: 'destructive',
      });
      return;
    }

    setIsAnalyzing(true);
    
    try {
      // Simulate AI analysis - in real implementation, this would call an AI service
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockInsights = {
        strengths: [
          'Strong technical skills in React and Node.js',
          'Good experience with modern development practices',
          'Clear career progression shown'
        ],
        improvements: [
          'Add more quantified achievements (e.g., "increased performance by 40%")',
          'Include relevant certifications',
          'Expand on leadership experiences'
        ],
        marketTrends: [
          'Full-stack developers with React skills are in high demand',
          'Companies are looking for cloud experience (AWS/Azure)',
          'Remote work opportunities are increasing'
        ],
        recommendations: [
          'Consider learning TypeScript to increase job matches',
          'Add Docker/Kubernetes experience for better opportunities',
          'Highlight any open-source contributions'
        ]
      };

      setAiInsights(mockInsights);
      
      toast({
        title: 'Analysis Complete!',
        description: 'AI has analyzed your resume and provided insights',
      });
    } catch (error) {
      toast({
        title: 'Analysis Failed',
        description: 'Failed to analyze resume. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="flex min-h-screen items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Welcome back, Candidate</h1>
          <p className="text-muted-foreground">Track your job search progress and discover new opportunities.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Resumes</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalResumes}</div>
              <p className="text-xs text-muted-foreground">
                Uploaded and parsed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Job Matches</CardTitle>
              <Briefcase className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.jobMatches}</div>
              <p className="text-xs text-muted-foreground">
                Potential opportunities
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Profile Views</CardTitle>
              <Eye className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.profileViews}</div>
              <p className="text-xs text-muted-foreground">
                By recruiters
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Skills</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.skillsExtracted}</div>
              <p className="text-xs text-muted-foreground">
                Extracted from resume
              </p>
            </CardContent>
          </Card>
        </div>

        {/* AI Assistant and Tools */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* AI Career Assistant */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-primary" />
                  AI Career Assistant
                </CardTitle>
                <CardDescription>Get personalized career guidance and job search advice</CardDescription>
              </CardHeader>
              <CardContent>
                <AIChat
                  context="candidate_assistance"
                  title=""
                  placeholder="Ask about jobs, career advice, resume tips..."
                  className="h-80"
                  triggerMessage={quickPrompt}
                />
                
                {/* Quick Starter Prompts */}
                <div className="mt-4 space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">Quick questions:</p>
                  <div className="flex flex-wrap gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setQuickPrompt("How can I improve my resume for tech jobs?")}
                    >
                      Resume Tips
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setQuickPrompt("What are the best interview preparation strategies?")}
                    >
                      Interview Prep
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setQuickPrompt("What skills should I learn to advance my career?")}
                    >
                      Skill Development
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Get started with your job search</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button className="w-full justify-start" variant="outline">
                  <Upload className="mr-2 h-4 w-4" />
                  Upload New Resume
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <Briefcase className="mr-2 h-4 w-4" />
                  Browse Jobs
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <FileText className="mr-2 h-4 w-4" />
                  Edit Skills
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  AI Career Chat
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* AI Resume Analyzer */}
          <div className="lg:col-span-1">
            {resumes.length === 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-primary" />
                    AI Resume Analyzer
                  </CardTitle>
                  <CardDescription>Upload a resume to get personalized insights</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResumeDropzone 
                    onFileSelected={(file) => {
                      setUploadedFile(file);
                      const mockResume = {
                        id: 'local-' + Date.now(),
                        filename: file.name,
                        created_at: new Date().toISOString(),
                        parsing_status: 'uploaded',
                        size: file.size,
                      } as any;
                      setResumes([mockResume]);
                    }}
                  />
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5 text-primary" />
                    AI Resume Analyzer
                  </CardTitle>
                  <CardDescription>Get intelligent insights about your resume</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {resumes.map((resume: any) => (
                      <div key={resume.id} className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{resume.filename}</p>
                          <p className="text-sm text-muted-foreground">
                            {new Date(resume.created_at).toLocaleDateString()} {resume.size ? `• ${(resume.size / 1024 / 1024).toFixed(2)} MB` : ''}
                          </p>
                        </div>
                        <Badge variant={resume.parsing_status === 'completed' ? "default" : "secondary"}>
                          {resume.parsing_status}
                        </Badge>
                      </div>
                    ))}

                    <Button 
                      onClick={() => {
                        if (!uploadedFile) {
                          toast({ title: 'No file', description: 'Please upload a resume first.' });
                          return;
                        }
                        analyzeResume(uploadedFile);
                        runAIAnalysis();
                      }} 
                      disabled={isAnalyzing}
                      className="w-full"
                    >
                      <Zap className="mr-2 h-4 w-4" />
                      {isAnalyzing ? 'Analyzing...' : 'Run AI Analysis'}
                    </Button>
                    
                    <ResumeDropzone 
                      small
                      onFileSelected={(file) => {
                        setUploadedFile(file);
                        const mockResume = {
                          id: 'local-' + Date.now(),
                          filename: file.name,
                          created_at: new Date().toISOString(),
                          parsing_status: 'uploaded',
                          size: file.size,
                        } as any;
                        setResumes([mockResume]);
                      }}
                    />
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* AI Insights Section */}
        {(aiInsights.strengths.length > 0 || aiInsights.improvements.length > 0) && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                AI Resume Insights
              </CardTitle>
              <CardDescription>Intelligent analysis and recommendations for your resume</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Strengths */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <h3 className="font-semibold">Strengths</h3>
                  </div>
                  <div className="space-y-2">
                    {aiInsights.strengths.map((strength, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-sm">{strength}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Improvements */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-yellow-600" />
                    <h3 className="font-semibold">Areas for Improvement</h3>
                  </div>
                  <div className="space-y-2">
                    {aiInsights.improvements.map((improvement, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-sm">{improvement}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Market Trends */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-blue-600" />
                    <h3 className="font-semibold">Market Trends</h3>
                  </div>
                  <div className="space-y-2">
                    {aiInsights.marketTrends.map((trend, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-sm">{trend}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Target className="h-5 w-5 text-purple-600" />
                    <h3 className="font-semibold">Recommendations</h3>
                  </div>
                  <div className="space-y-2">
                    {aiInsights.recommendations.map((recommendation, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-sm">{recommendation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Job Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle>Recommended Jobs</CardTitle>
            <CardDescription>Jobs that match your skills and experience</CardDescription>
          </CardHeader>
          <CardContent>
            {recentMatches.length > 0 ? (
              <div className="space-y-4">
                {recentMatches.map((match: any) => (
                  <div key={match.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{match.jobs?.title}</h4>
                        <Badge variant="outline">
                          {Math.round(match.fit_score * 100)}% match
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {match.jobs?.companies?.name}
                      </p>
                      <div className="flex items-center space-x-4">
                        <div className="flex-1">
                          <div className="flex justify-between text-sm mb-1">
                            <span>Skills Match</span>
                            <span>{match.skill_match_count}/{match.total_required_skills}</span>
                          </div>
                          <Progress 
                            value={(match.skill_match_count / Math.max(match.total_required_skills, 1)) * 100} 
                            className="h-2"
                          />
                        </div>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" className="ml-4">
                      View Job
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">
                  No job matches yet. Upload a resume to get personalized recommendations!
                </p>
                <Button variant="outline">
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Resume
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
};

export default CandidateDashboard;

// Local, backend-free resume dropzone component
const ResumeDropzone: React.FC<{
  onFileSelected: (file: File) => void;
  small?: boolean;
}> = ({ onFileSelected, small }) => {
  const { toast } = useToast();
  const inputId = React.useId();

  const ACCEPTED = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
  ];
  const MAX_MB = 10;

  const handleFiles = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    const file = fileList[0];

    if (!ACCEPTED.includes(file.type) && !file.name.toLowerCase().endsWith('.docx') && !file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.txt')) {
      toast({ title: 'Unsupported file', description: 'Please upload a PDF, DOCX, or TXT file.', variant: 'destructive' });
      return;
    }

    if (file.size > MAX_MB * 1024 * 1024) {
      toast({ title: 'File too large', description: `Maximum size is ${MAX_MB} MB.`, variant: 'destructive' });
      return;
    }

    onFileSelected(file);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <div>
      <label htmlFor={inputId} className={`block w-full border-2 border-dashed rounded-lg text-center cursor-pointer hover:bg-muted/40 transition ${small ? 'p-3' : 'p-6'}`} onDrop={onDrop} onDragOver={onDragOver}>
        <div className="flex flex-col items-center gap-2">
          <Upload className="h-5 w-5 text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">{small ? 'Upload Resume' : 'Drop your resume here or click to upload'}</p>
            <p className="text-xs text-muted-foreground">PDF, DOCX, or TXT up to 10MB</p>
          </div>
        </div>
      </label>
      <input
        id={inputId}
        type="file"
        accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  );
};

// Placeholder to show where the AI call would occur later
function analyzeResume(file: File) {
  // eslint-disable-next-line no-console
  console.log('Analyzing resume (placeholder):', file.name, file.size, file.type);
}