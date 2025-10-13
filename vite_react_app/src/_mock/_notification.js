import { useEffect } from 'react';
import { gql, useQuery } from '@apollo/client';

import { CONFIG } from 'src/config-global';

const GET_NOTIFICATIONS = gql`
  query GetNotifications($username: String) {
    allNotificationUser(username: $username) {
      id
      username
      createdAt
      updatedAt
      read
      notification {
        id
        module
        info
        type
        createdAt
        updatedAt
      }
      user {
        username
        firstName
        lastName
      }
    }
  }
`;

export const useNotificationsQuery = (username) => {
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_NOTIFICATIONS, {
    variables: { username },
    skip: !username,
  });

  return { loading, error, data: data?.allNotificationUser || [] };
};
