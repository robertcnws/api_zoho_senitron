import { useEffect } from 'react';
import { gql, useQuery } from '@apollo/client';

const GET_MANUAL_UPDATING_JOBS = gql`
  {
      allManualUpdatingJobs {
        id
        isRunning
      }
  }
`;

export const useManualUpdatingJobsQuery = () => {
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_MANUAL_UPDATING_JOBS);

  useEffect(() => {
    startPolling(5000); 
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  return { loading, error, data: data?.allManualUpdatingJobs };
};
