import { Helmet } from 'react-helmet-async';
import React, { useState, useEffect, useCallback } from 'react';

import { useParams } from 'src/routes/hooks';

import { useWebsocket } from 'src/hooks/use-websocket';

import { CONFIG } from 'src/config-global';
import { useShipmentsQuery } from 'src/_mock/_shipment';

import { ShipmentDetailsView } from 'src/sections/shipment/view';

// ----------------------------------------------------------------------

const metadata = { title: `Order details | Dashboard - ${CONFIG.appName}` };

export default function Page() {
  const { id = '' } = useParams();

  const { data, refetch: refetchShipments } = useShipmentsQuery(null, null);

  const [shipments, setShipments] = useState(null);

  const [currentShipment, setCurrentShipment] = useState(null);

  useEffect(() => {
    if (data && data?.length) {
      setShipments(data);
      setCurrentShipment(data.find((ship) => ship.shipmentId === id));
    }
  }, [id, data]);

  const baseWsUrl = `${CONFIG.websocketProtocol}://${CONFIG.apiHost}:${CONFIG.apiPort}/${CONFIG.apiDomain}/ws`;

  const onMessage = useCallback((m) => {
    if (['created', 'updated', 'deleted'].includes(m.type)) refetchShipments?.();
  }, [refetchShipments]);

  useWebsocket(`${baseWsUrl}/shipment_orders/`, onMessage);

  if (!currentShipment) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title> {metadata.title}</title>
      </Helmet>

      <ShipmentDetailsView shipment={currentShipment} />
    </>
  );
}
