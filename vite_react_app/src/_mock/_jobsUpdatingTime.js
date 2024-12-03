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
    const checkAndTogglePolling = () => {
      const now = new Date();
      const currentHour = now.getHours();
      
      if (currentHour >= 7 && currentHour < 17) {
        startPolling(5000);
      } else {
        stopPolling();
      }
    };

    checkAndTogglePolling();

    const intervalId = setInterval(checkAndTogglePolling, 5000); 

    return () => {
      clearInterval(intervalId);
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  return { loading, error, data: data?.allJobsUpdatingTimes };
};
