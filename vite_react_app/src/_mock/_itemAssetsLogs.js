import { useEffect } from 'react';
import { gql, useQuery } from '@apollo/client';

const GET_SENITRON_ITEMS_ASSETS_LOGS = gql`
  query GetSenitronGroupedLogs($startDate: Date) {
    allSenitronGroupedLogs(startDate: $startDate) {
      itemNumber
      date
      logs {
        senitronId
        serialNumber
        altSerial
        lastSeen
        lastZone
        epc
        lastStatusId
        lastStatusName
        currentStatusId
        currentStatusName
        user
        reason
        createdAt
        updatedAt
        createdTime
      }
    }
  }
`;

export const useSenitronAssetsLogsQuery = (startDate, endDate) => {
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_SENITRON_ITEMS_ASSETS_LOGS, {
    variables: { startDate, endDate },
  });

  useEffect(() => {
    startPolling(5000); 
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);
  
  return { loading, error, data: data?.allSenitronGroupedLogs };
};
