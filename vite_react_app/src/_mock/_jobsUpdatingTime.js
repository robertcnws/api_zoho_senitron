import { useEffect } from 'react';
import { gql, useQuery } from '@apollo/client';

const GET_JOBS_UPDTING_TIMES = gql`
  {
    allJobsUpdatingTimes {
        id
        lastUpdated
    }
  }
`;

export const useJobsUpdatingTimesQuery = () => {
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_JOBS_UPDTING_TIMES);

  useEffect(() => {
    startPolling(5000); 
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  return { loading, error, data: data?.allJobsUpdatingTimes };
};
