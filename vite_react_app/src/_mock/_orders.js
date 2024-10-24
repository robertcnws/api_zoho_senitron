import { gql, useQuery } from '@apollo/client';

const GET_ZOHO_INVENTORY_SALES_ORDERS = gql`
  query GetZohoInventorySalesOrders($startDate: String, $endDate: String) {
    allZohoInventorySalesOrders(startDate: $startDate, endDate: $endDate) {
      salesorderId
      salesorderNumber
      date
      status
      lineItems
    }
  }
`;

export const useSalesOrdersQuery = (startDate, endDate) => {
  const { loading, error, data } = useQuery(GET_ZOHO_INVENTORY_SALES_ORDERS, {
    variables: { startDate, endDate },
  });
  
  return { loading, error, data: data?.allZohoInventorySalesOrders };
};


export const SALES_ORDERS_STATUS_OPTIONS = [
  { value: 'fulfilled', label: 'Fulfilled' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'partially_shipped', label: 'Partially Shipped' },
  { value: 'draft', label: 'Draft' },
];
