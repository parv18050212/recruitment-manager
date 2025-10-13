import React from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import RecruiterDashboard from '@/components/dashboard/RecruiterDashboard';
import CandidateDashboard from '@/components/dashboard/CandidateDashboard';

const Dashboard = () => {
  const { profile } = useAuth();

  if (!profile) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {profile.role === 'recruiter' ? (
        <RecruiterDashboard />
      ) : (
        <CandidateDashboard />
      )}
    </div>
  );
};

export default Dashboard;