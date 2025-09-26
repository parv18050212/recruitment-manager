import React, { useState, useEffect } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { Upload, FileText, Briefcase, TrendingUp, Eye } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';

const CandidateDashboard = () => {
  const { profile } = useAuth();
  const { toast } = useToast();
  const [stats, setStats] = useState({
    totalResumes: 0,
    jobMatches: 0,
    profileViews: 0,
    skillsExtracted: 0
  });
  const [recentMatches, setRecentMatches] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch resume statistics
      const { data: resumeData } = await supabase
        .from('resumes')
        .select('*, resume_skills(*)')
        .eq('candidate_id', profile.id);

      // Fetch job matches
      const { data: matches } = await supabase
        .from('matches')
        .select('*, jobs(title, company_id, companies(name))')
        .eq('candidate_id', profile.id)
        .order('fit_score', { ascending: false })
        .limit(5);

      const totalSkills = resumeData?.reduce((acc, resume) => acc + (resume.resume_skills?.length || 0), 0) || 0;

      setStats({
        totalResumes: resumeData?.length || 0,
        jobMatches: matches?.length || 0,
        profileViews: 0, // This would come from analytics
        skillsExtracted: totalSkills
      });

      setRecentMatches(matches || []);
      setResumes(resumeData || []);
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

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
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
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resume Status</CardTitle>
              <CardDescription>Your uploaded resumes</CardDescription>
            </CardHeader>
            <CardContent>
              {resumes.length > 0 ? (
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
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-muted-foreground mb-4">No resumes uploaded yet</p>
                  <Button variant="outline" size="sm">
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Your First Resume
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
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