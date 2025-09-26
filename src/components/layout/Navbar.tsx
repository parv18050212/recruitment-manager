import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/components/auth/AuthProvider';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { User, LogOut, Settings, Briefcase, Upload } from 'lucide-react';

const Navbar = () => {
  const { user, profile, signOut } = useAuth();
  const location = useLocation();

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase();
  };

  const handleSignOut = async () => {
    await signOut();
  };

  if (!user) {
    return null;
  }

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">TM</span>
              </div>
              <span className="font-bold text-xl">TalentMatch</span>
            </Link>
            
            {profile && (
              <div className="hidden md:flex items-center space-x-6">
                <Link
                  to="/dashboard"
                  className={`text-sm font-medium transition-colors hover:text-primary ${
                    location.pathname === '/dashboard'
                      ? 'text-foreground'
                      : 'text-muted-foreground'
                  }`}
                >
                  Dashboard
                </Link>
                
                {profile.role === 'recruiter' && (
                  <>
                    <Link
                      to="/jobs"
                      className={`text-sm font-medium transition-colors hover:text-primary ${
                        location.pathname === '/jobs'
                          ? 'text-foreground'
                          : 'text-muted-foreground'
                      }`}
                    >
                      Jobs
                    </Link>
                    <Link
                      to="/candidates"
                      className={`text-sm font-medium transition-colors hover:text-primary ${
                        location.pathname === '/candidates'
                          ? 'text-foreground'
                          : 'text-muted-foreground'
                      }`}
                    >
                      Candidates
                    </Link>
                  </>
                )}
                
                {profile.role === 'candidate' && (
                  <>
                    <Link
                      to="/jobs"
                      className={`text-sm font-medium transition-colors hover:text-primary ${
                        location.pathname === '/jobs'
                          ? 'text-foreground'
                          : 'text-muted-foreground'
                      }`}
                    >
                      Find Jobs
                    </Link>
                    <Link
                      to="/resume"
                      className={`text-sm font-medium transition-colors hover:text-primary ${
                        location.pathname === '/resume'
                          ? 'text-foreground'
                          : 'text-muted-foreground'
                      }`}
                    >
                      My Resume
                    </Link>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-4">
            {profile && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={profile.avatar_url} alt={profile.full_name} />
                      <AvatarFallback>
                        {getInitials(profile.full_name)}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <div className="flex flex-col space-y-1 p-2">
                    <p className="text-sm font-medium leading-none">{profile.full_name}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user.email}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground capitalize">
                      {profile.role}
                    </p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/profile" className="flex items-center">
                      <User className="mr-2 h-4 w-4" />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/settings" className="flex items-center">
                      <Settings className="mr-2 h-4 w-4" />
                      Settings
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleSignOut}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;