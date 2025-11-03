import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: any | null;
  loading: boolean;
  signUp: (email: string, password: string, userData: any) => Promise<{ error: any }>;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
  updateProfile: (data: any) => Promise<{ error: any }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Helper to fetch or create profile for the current user
    const fetchOrCreateProfile = async (currentUser: User) => {
      // Try fetch existing profile
      const { data: existingProfile, error: fetchError } = await supabase
        .from('profiles')
        .select('*')
        .eq('user_id', currentUser.id)
        .single();

      if (!fetchError && existingProfile) {
        return existingProfile;
      }

      // If not found, create a minimal profile using user metadata
      const metadata = currentUser.user_metadata || {};
      const insertPayload = {
        user_id: currentUser.id,
        email: currentUser.email,
        full_name: metadata.full_name ?? '',
        role: metadata.role ?? 'candidate',
        phone: metadata.phone ?? null,
        location: metadata.location ?? null,
      };

      const { data: createdProfile } = await supabase
        .from('profiles')
        .insert(insertPayload)
        .select('*')
        .single();

      return createdProfile ?? null;
    };

    // Set up auth state listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, nextSession) => {
        setLoading(true);
        setSession(nextSession);
        const nextUser = nextSession?.user ?? null;
        setUser(nextUser);

        if (nextUser) {
          const p = await fetchOrCreateProfile(nextUser);
          setProfile(p);
        } else {
          setProfile(null);
        }
        setLoading(false);
      }
    );

    // Get initial session and ensure profile exists before clearing loading
    (async () => {
      const { data: { session: initialSession } } = await supabase.auth.getSession();
      setSession(initialSession);
      const initialUser = initialSession?.user ?? null;
      setUser(initialUser);
      if (initialUser) {
        const p = await fetchOrCreateProfile(initialUser);
        setProfile(p);
      } else {
        setProfile(null);
      }
      setLoading(false);
    })();

    return () => subscription.unsubscribe();
  }, []);

  const signUp = async (email: string, password: string, userData: any) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/`,
        data: userData
      }
    });
    return { error };
  };

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { error };
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  const updateProfile = async (data: any) => {
    if (!user) return { error: new Error('No user logged in') };
    
    const { error } = await supabase
      .from('profiles')
      .update(data)
      .eq('user_id', user.id);
    
    if (!error) {
      setProfile({ ...profile, ...data });
    }
    
    return { error };
  };

  const value = {
    user,
    session,
    profile,
    loading,
    signUp,
    signIn,
    signOut,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};