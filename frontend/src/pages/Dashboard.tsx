import React from 'react';
import RecruiterDashboard from '@/components/dashboard/RecruiterDashboard';
import CandidateDashboard from '@/components/dashboard/CandidateDashboard';

// Mock guest user object to replace auth profile
const guestUser = {
  id: 'guest-user-id',
  full_name: 'Guest User',
  role: 'recruiter' as 'recruiter' | 'candidate',
  email: 'guest@example.com',
  phone: '',
  location: '',
  avatar_url: null,
};

const Dashboard = () => {
  // Default to recruiter dashboard for guest users
  // You can change this to 'candidate' if you prefer
  const userRole = guestUser.role;

  return (
    <div className="min-h-screen bg-background">
      {userRole === 'recruiter' ? (
        <RecruiterDashboard />
      ) : (
        <CandidateDashboard />
      )}
    </div>
  );
};

export default Dashboard;