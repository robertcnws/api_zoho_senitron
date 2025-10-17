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
  const { loading, error, data, refetch } = useQuery(GET_MANUAL_UPDATING_JOBS);

  return { loading, error, data: data?.allManualUpdatingJobs || [], refetch };
};
