import { createClient } from '@supabase/supabase-js';
import type { Database } from './types';

// Read from Vite env; never hardcode credentials in the repo
// Strip quotes in case they're included in .env.local
const SUPABASE_URL = (import.meta.env.VITE_SUPABASE_URL as string | undefined)?.replace(/^["']|["']$/g, '');
const SUPABASE_ANON_KEY = (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined)?.replace(/^["']|["']$/g, '');

// Debug logging (remove in production)
if (SUPABASE_URL && SUPABASE_ANON_KEY) {
  console.log('✅ Supabase configured:', {
    url: SUPABASE_URL,
    hasKey: !!SUPABASE_ANON_KEY,
    keyLength: SUPABASE_ANON_KEY?.length
  });
} else {
  console.warn('⚠️ Supabase not configured:', {
    hasUrl: !!SUPABASE_URL,
    hasKey: !!SUPABASE_ANON_KEY
  });
}

// Import the supabase client like this:
// import { supabase } from "@/integrations/supabase/client";

// If env is missing, provide a safe fallback that won't crash the app at import time.
// It logs guidance and returns no-op auth handlers so the UI can still render.
const createSafeFallbackClient = () => {
  const guidance =
    'Supabase is not configured. Create frontend/.env.local with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY, then restart dev server.';
  // Minimal surface used by the app
  const fallbackAuth = {
    onAuthStateChange: () => {
      console.error(guidance);
      return { data: { subscription: { unsubscribe: () => {} } } } as any;
    },
    getSession: async () => {
      console.error(guidance);
      return { data: { session: null } } as any;
    },
    signUp: async () => {
      console.error(guidance);
      return { error: new Error(guidance) } as any;
    },
    signInWithPassword: async () => {
      console.error(guidance);
      return { error: new Error(guidance) } as any;
    },
    signOut: async () => {
      console.error(guidance);
    },
  };
  return { auth: fallbackAuth } as any;
};

// Validate URL format
const isValidSupabaseUrl = (url: string | undefined): url is string => {
  if (!url) return false;
  return /^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(url);
};

export const supabase =
  SUPABASE_URL && SUPABASE_ANON_KEY && isValidSupabaseUrl(SUPABASE_URL)
    ? createClient<Database>(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
          storage: localStorage,
          persistSession: true,
          autoRefreshToken: true,
          flowType: 'pkce'
        }
      })
    : (() => {
        if (SUPABASE_URL && !isValidSupabaseUrl(SUPABASE_URL)) {
          console.error('❌ Invalid Supabase URL format:', SUPABASE_URL);
          console.error('Expected format: https://PROJECT_REF.supabase.co');
        }
        return createSafeFallbackClient();
      })();