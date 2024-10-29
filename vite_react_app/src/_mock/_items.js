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

export const useItemsQuery = () => {
  const { loading, error, data } = useQuery(GET_ZOHO_INVENTORY_ITEMS);
  return { loading, error, data: data?.allZohoInventoryItems };
};

export const ITEM_STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'confirmation_pending', label: 'Confirmation Pending' },
  { value: 'inactive', label: 'Inactive' },
];

export const ITEM_SYNC_OPTIONS = [
  { value: 'yes', label: 'Synced' },
  { value: 'no', label: 'Not Synced' },
];
