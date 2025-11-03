import React from 'react';
import RecruiterDashboard from '@/components/dashboard/RecruiterDashboard';
import CandidateDashboard from '@/components/dashboard/CandidateDashboard';

const Dashboard = () => {
  // Render candidate dashboard by default; if you want recruiter view, swap below
  // or add a simple local toggle/state later without auth.

  return (
    <div className="min-h-screen bg-background">
      <CandidateDashboard />
    </div>
  );
};

export default Dashboard;