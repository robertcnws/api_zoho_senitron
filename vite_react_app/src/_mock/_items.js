import { gql, useQuery } from '@apollo/client';

const GET_ZOHO_INVENTORY_ITEMS = gql`
  {
    allZohoInventoryItems {
       itemId
       sku
       name
       status
       stockOnHand
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
