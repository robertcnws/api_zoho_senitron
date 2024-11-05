import { useEffect } from 'react';
import { gql, useQuery } from '@apollo/client';

const GET_ZOHO_INVENTORY_ITEMS = gql`
  {
    allZohoInventoryItems {
        id
        groupId
        groupName
        itemId
        name
        status
        source
        itemType
        isLinkedWithZohocrm
        description
        rate
        isTaxable
        taxId
        taxName
        taxPercentage
        purchaseDescription
        purchaseRate
        isComboProduct
        syncedWithSenitron
        productType
        attributeId1
        attributeName1
        reorderLevel
        stockOnHand
        availableStock
        actualAvailableStock
        sku
        upc
        ean
        isbn
        partNumber
        attributeOptionId1
        attributeOptionName1
        createdTime
        lastModifiedTime
        hsnOrSac
        satItemKeyCode
        unitkeyCode
    }
  }
`;

const GET_SENITRON_INVENTORY_ITEM = gql`
  {
    allSenitronInventoryItemsAssets {
      id
      serialNumber
      itemNumber
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
      senitronItem {
        itemNumber
        tagsCount
        qty
      }
      status {
        name
        id
      }
    }
  }
`;

export const useItemsQuery = () => {
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_ZOHO_INVENTORY_ITEMS);

  useEffect(() => {
    startPolling(5000); 
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
  { value: 'active', label: 'Active' },
  { value: 'confirmation_pending', label: 'Confirmation Pending' },
  { value: 'inactive', label: 'Inactive' },
];

export const ITEM_STATUS_SHORT_OPTIONS = [
  { value: 'active', label: 'Items Active' },
  { value: 'confirmation_pending', label: 'Items in Confirmation Pending' },
  { value: 'inactive', label: 'Items Inactive' },
];

export const ITEM_SYNC_OPTIONS = [
  { value: 'yes', label: 'Synced' },
  { value: 'no', label: 'Not Synced' },
];
