import React, { useState, useEffect } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { PlusCircle, Users, Briefcase, TrendingUp, Upload } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';

const RecruiterDashboard = () => {
  const { profile } = useAuth();
  const { toast } = useToast();
  const [stats, setStats] = useState({
    totalJobs: 0,
    activeJobs: 0,
    totalCandidates: 0,
    newMatches: 0
  });
  const [recentJobs, setRecentJobs] = useState([]);
  const [topMatches, setTopMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch job statistics
      const { data: jobs } = await supabase
        .from('jobs')
        .select('*')
        .eq('recruiter_id', profile.id);

      // Fetch matches statistics
      const { data: matches } = await supabase
        .from('matches')
        .select('*, resumes(*, profiles(full_name)), jobs(title)')
        .eq('recruiter_id', profile.id)
        .order('fit_score', { ascending: false })
        .limit(5);

      setStats({
        totalJobs: jobs?.length || 0,
        activeJobs: jobs?.filter(job => job.is_active).length || 0,
        totalCandidates: matches?.length || 0,
        newMatches: matches?.filter(match => {
          const createdAt = new Date(match.created_at);
          const oneWeekAgo = new Date();
          oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
          return createdAt > oneWeekAgo;
        }).length || 0
      });

      setRecentJobs(jobs?.slice(0, 3) || []);
      setTopMatches(matches || []);
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
          <p className="text-muted-foreground">Here's what's happening with your recruitment.</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
              <Briefcase className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalJobs}</div>
              <p className="text-xs text-muted-foreground">
                {stats.activeJobs} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Candidates</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalCandidates}</div>
              <p className="text-xs text-muted-foreground">
                Total matched candidates
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">New Matches</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.newMatches}</div>
              <p className="text-xs text-muted-foreground">
                This week
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">85%</div>
              <p className="text-xs text-muted-foreground">
                Matching accuracy
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Get started with common tasks</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button className="w-full justify-start" variant="outline">
                <PlusCircle className="mr-2 h-4 w-4" />
                Create New Job Posting
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                Upload Resumes
              </Button>
              <Button className="w-full justify-start" variant="outline">
                <Users className="mr-2 h-4 w-4" />
                View All Candidates
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Jobs</CardTitle>
              <CardDescription>Your latest job postings</CardDescription>
            </CardHeader>
            <CardContent>
              {recentJobs.length > 0 ? (
                <div className="space-y-4">
                  {recentJobs.map((job: any) => (
                    <div key={job.id} className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{job.title}</p>
                        <p className="text-sm text-muted-foreground">{job.location}</p>
                      </div>
                      <Badge variant={job.is_active ? "default" : "secondary"}>
                        {job.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No jobs posted yet</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Top Matches */}
        <Card>
          <CardHeader>
            <CardTitle>Top Candidate Matches</CardTitle>
            <CardDescription>Best candidates for your open positions</CardDescription>
          </CardHeader>
          <CardContent>
            {topMatches.length > 0 ? (
              <div className="space-y-4">
                {topMatches.map((match: any) => (
                  <div key={match.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{match.resumes?.profiles?.full_name}</h4>
                        <Badge variant="outline">
                          {Math.round(match.fit_score * 100)}% match
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        {match.jobs?.title}
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
                      View Profile
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No matches found yet</p>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
};

export default RecruiterDashboard;