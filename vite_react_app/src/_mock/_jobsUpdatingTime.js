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
        startPolling(900000); // 15 minutos
      } else {
        stopPolling();
      }
    };

    checkAndTogglePolling();

    const intervalId = setInterval(checkAndTogglePolling, 60000); // Cada minuto

    return () => {
      clearInterval(intervalId);
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  return { loading, error, data: data?.allJobsUpdatingTimes };
};
