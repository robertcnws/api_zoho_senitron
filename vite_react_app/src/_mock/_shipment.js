import { useMemo } from 'react';
import { gql, useQuery } from '@apollo/client';


const GET_ZOHO_SHIPMENT_ORDERS = gql`
  query GetZohoShipmentOrders($startDate: String, $endDate: String) {
    allZohoShipmentOrders(startDate: $startDate, endDate: $endDate) {
      shipmentId
      salesorderId
      salesorderNumber
      salesorderDate
      salesorderFulfilmentStatus
      salesChannel
      salesChannelFormatted
      shipmentNumber
      date
      shipmentStatus
      shipmentSubStatus
      status
      detailedStatus
      statusMessage
      carrier
      trackingCarrierCode
      service
      deliveryDays
      sourceId
      labelFormat
      sourceName
      deliveryGuarantee
      referenceNumber
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
      discount
      isDiscountBeforeTax
      discountType
      estimateId
      deliveryMethod
      deliveryMethodId
      trackingNumber
      trackingLink
      expectedDeliveryDate
      shipmentDeliveredDate
      shipmentType
      isCarrierShipment
      isTrackingEnabled
      isFormsAvailable
      isEmailNotificationEnabled
      shippingCharge
      subTotal
      taxTotal
      total
      pricePrecision
      isEmailed
      notes
      templateId
      templateName
      templateType
      createdTime
      lastModifiedTime
      associatedPackagesCount
      createdById
      lastModifiedById
      contactPersons
      invoices
      lineItems
      packages
      billingAddress
      shippingAddress
      customFields
      customFieldHash
      documents
      taxes
      trackingStatuses
      multipieceShipments
    }
  }
`;

const buildVars = (startDate, endDate) => {
  const v = {};
  if (startDate) v.startDate = startDate;
  if (endDate) v.endDate = endDate;
  return v;
};

export const useShipmentsQuery = (startDate, endDate) => {
  const variables = useMemo(() => buildVars(startDate, endDate), [startDate, endDate]);
  const { loading, error, data, refetch } = useQuery(GET_ZOHO_SHIPMENT_ORDERS, {
    variables,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  return { loading, error, data: data?.allZohoShipmentOrders || [], refetch };
};


export const SHIPMENTS_STATUS_OPTIONS = [
  { value: 'delivered', label: 'Delivered' },
  { value: 'partially_shipped', label: 'Partially Shipped' },
  { value: 'draft', label: 'Draft' },
];
