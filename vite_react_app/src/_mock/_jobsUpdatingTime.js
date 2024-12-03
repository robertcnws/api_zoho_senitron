import { useEffect } from 'react';
import { gql, useQuery } from '@apollo/client';

const GET_ZOHO_INVENTORY_ITEMS = gql`
  {
    allJobsUpdatingTime {
        id
        lastUpdated
    }
  }
`;

const GET_SENITRON_INVENTORY_ITEM = gql`
  {
    allSenitronInventoryItemsAssets {
      itemNumber
      count
      senitronItem {
        itemNumber
        tagsCount
        qty
      }
      assets {
        id
        serialNumber
        altSerial
        firstSeen
        lastSeen
        lastSeenAntenna
        lastZone
        handheldReader
        handheldLastSeen
        staticZone
        staticZoneLastUpdate
        receivingDate
        currentUnits
        storageUnit
        adjustQty
        createdAt
        updatedAt
        epc
        text3
        status {
          id
          name
        }
      }
    }
  }
`;

export const useItemsQuery = () => {
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_ZOHO_INVENTORY_ITEMS);

  useEffect(() => {
    startPolling(900000); 
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  return { loading, error, data: data?.allZohoInventoryItems };
};

export const useSenitronItemsQuery = () => {
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_SENITRON_INVENTORY_ITEM);

  useEffect(() => {
    startPolling(5000); 
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);

  return { loading, error, data: data?.allSenitronInventoryItemsAssets };
};

export const ITEM_STATUS_OPTIONS = [
  // { value: 'active', label: 'Active' },
  // { value: 'confirmation_pending', label: 'Confirmation Pending' },
  // { value: 'inactive', label: 'Inactive' },
];

export const ITEM_TYPE_OPTIONS = [
  { value: 'not_synced', label: 'SKUs Untracked' },
  { value: 'active', label: 'SKUs Active' },
  { value: 'inactive', label: 'SKUs Inactive' },
  { value: 'confirmation_pending', label: 'SKUs in Confirmation Pending' },
  { value: 'not_assets', label: 'SKUs without Assets' },
];

export const ITEM_STATUS_SHORT_OPTIONS = [
  // { value: 'all', label: 'All Items' }, 
  // { value: 'active', label: 'Items Active' },
  // { value: 'confirmation_pending', label: 'Items in Confirmation Pending' },
  // { value: 'inactive', label: 'Items Inactive' },
];

export const ITEM_SYNC_OPTIONS = [
  { value: 'yes', label: 'Synced' },
  { value: 'no', label: 'Not Synced' },
];
