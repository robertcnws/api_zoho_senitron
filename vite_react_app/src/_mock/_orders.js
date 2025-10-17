import { useMemo } from 'react';
import { gql, useQuery } from '@apollo/client';


const GET_ZOHO_INVENTORY_SALES_ORDERS = gql`
  query GetZohoInventorySalesOrders($startDate: String, $endDate: String) {
    allZohoInventorySalesOrders(startDate: $startDate, endDate: $endDate) {
      salesorderId
      salesorderNumber
      date
      status
      lineItems
      customerId
      customerName
      isTaxable
      taxId
      taxName
      taxPercentage
      currencyId
      currencyCode
      currencySymbol
      exchangeRate
      deliveryMethod
      totalQuantity
      subTotal
      taxTotal
      total
      createdByEmail
      createdByName
      salespersonId
      isTestOrder
      notes
      paymentTerms
      paymentTermsLabel
      shippingAddress
      billingAddress
      warehouses
      customFields
      orderSubStatuses
      shipmentSubStatuses
      createdTime
      lastModifiedTime
    }
  }
`;

const buildVars = (startDate, endDate) => {
  const v = {};
  if (startDate) v.startDate = startDate;
  if (endDate) v.endDate = endDate;
  return v;
};

export const useSalesOrdersQuery = (startDate, endDate) => {
  const variables = useMemo(() => buildVars(startDate, endDate), [startDate, endDate]);
  const { loading, error, data, refetch } = useQuery(GET_ZOHO_INVENTORY_SALES_ORDERS, {
    variables,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  return { loading, error, data: data?.allZohoInventorySalesOrders || [], refetch };
};


export const SALES_ORDERS_STATUS_OPTIONS = [
  { value: 'fulfilled', label: 'Fulfilled' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'partially_shipped', label: 'Partially Shipped' },
  { value: 'draft', label: 'Draft' },
];
