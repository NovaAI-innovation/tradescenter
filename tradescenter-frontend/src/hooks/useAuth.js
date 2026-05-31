import { useCallback, useEffect, useState } from "react";
import { authApi, session } from "../api/client";

export function useAuth() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    const token = session.get();
    if (!token) {
      setProfile(null);
      setLoading(false);
      return;
    }

    try {
      const response = await authApi.me();
      setProfile(response.profile);
    } catch {
      session.clear();
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  return { profile, setProfile, loading, refreshProfile };
}
