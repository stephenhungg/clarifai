/**
 * Supabase client configuration for authentication
 */

import { createClient } from '@supabase/supabase-js'

// Get Supabase URL and key from environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// Create Supabase client for client components
// If Supabase is not configured, create a dummy client that will fail gracefully
export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey)
  : createClient('https://placeholder.supabase.co', 'placeholder-key')

// Check if Supabase is properly configured
export const isSupabaseConfigured = () => {
  return !!(supabaseUrl && supabaseAnonKey && 
    supabaseUrl !== '' && 
    supabaseAnonKey !== '' &&
    supabaseUrl !== 'https://placeholder.supabase.co')
}

/**
 * Get the current session token for API requests
 * @returns JWT token or null if not authenticated
 */
export async function getSessionToken(): Promise<string | null> {
  try {
    console.log('[SUPABASE] getSessionToken: Checking session...');
    const { data, error } = await supabase.auth.getSession()
    if (error) {
      console.error('[SUPABASE] getSessionToken: Error:', error);
      return null;
    }
    if (data.session) {
      console.log('[SUPABASE] getSessionToken: Session found, token length:', data.session.access_token?.length || 0);
      return data.session.access_token || null;
    } else {
      console.log('[SUPABASE] getSessionToken: No session found');
      return null;
    }
  } catch (error) {
    console.error('[SUPABASE] getSessionToken: Exception:', error)
    return null
  }
}

/**
 * Check if user is currently authenticated
 * @returns true if user has active session
 */
export async function isAuthenticated(): Promise<boolean> {
  const { data } = await supabase.auth.getSession()
  return !!data.session
}

/**
 * Sign out current user
 */
export async function signOut(): Promise<void> {
  await supabase.auth.signOut()
}

/**
 * Sign in with Google OAuth
 * @param redirectTo Optional redirect URL after successful login
 */
export async function signInWithGoogle(redirectTo?: string): Promise<void> {
  await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: redirectTo || `${window.location.origin}/papers`,
    },
  })
}
