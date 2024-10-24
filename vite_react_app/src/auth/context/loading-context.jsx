// LoadingContext.js
import React, { createContext, useState, useMemo } from 'react';

export const LoadingContext = createContext();

export function LoadingProvider({ children }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [component, setComponent] = useState(null);

  const value = useMemo(
    () => ({ loading, setLoading, error, setError, component, setComponent }),
    [loading, error, component]
  );

  return (
    <LoadingContext.Provider value={value}>
      {children}
    </LoadingContext.Provider>
  );
}
