import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { Upload, FileText, Briefcase, TrendingUp, Eye, MessageSquare } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import { AIChat } from '@/components/ai/AIChat';
import { ResumeUpload } from '@/components/ai/ResumeUpload';

// Mock guest profile for guest users
const guestProfile = {
  id: 'guest-user-id',
  full_name: 'Guest User',
  role: 'candidate',
  email: 'guest@example.com',
};

const CandidateDashboard = () => {
  const profile = guestProfile;
  const { toast } = useToast();
  const [stats, setStats] = useState({
    totalResumes: 0,
    jobMatches: 0,
    profileViews: 0,
    skillsExtracted: 0
  });
  const [recentMatches, setRecentMatches] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // For guest users, we'll use mock data or empty results
      // Remove database queries that require user authentication
      setStats({
        totalResumes: 0,
        jobMatches: 0,
        profileViews: 0,
        skillsExtracted: 0
      });
      setRecentMatches([]);
      setResumes([]);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
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
          <h1 className="text-3xl font-bold">Welcome back, {profile.full_name}</h1>
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
            <AIChat
              context="candidate_assistance"
              title="Career Assistant"
              placeholder="Ask about jobs, career advice, resume tips..."
              className="h-96"
            />
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

          {/* Resume Upload & Status */}
          <div className="lg:col-span-1">
            {resumes.length === 0 ? (
              <ResumeUpload
                onUploadComplete={(resumeData) => {
                  setResumes([resumeData]);
                  fetchDashboardData(); // Refresh data
                }}
              />
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Resume Status</CardTitle>
                  <CardDescription>Your uploaded resumes</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {resumes.map((resume: any) => (
                      <div key={resume.id} className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{resume.filename}</p>
                          <p className="text-sm text-muted-foreground">
                            {new Date(resume.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <Badge variant={resume.parsing_status === 'completed' ? "default" : "secondary"}>
                          {resume.parsing_status}
                        </Badge>
                      </div>
                    ))}
                    <Button variant="outline" className="w-full" size="sm">
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Another Resume
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

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