import { Helmet } from 'react-helmet-async';
import React, { useState, useEffect, useCallback } from 'react';

import { useParams } from 'src/routes/hooks';

import { CONFIG } from 'src/config-global';
import { useItemsQuery, useSenitronItemsQuery } from 'src/_mock/_items';

import { ItemDetailsView } from 'src/sections/item/view';
import { useWebsocket } from 'src/hooks/use-websocket';

// ----------------------------------------------------------------------

const metadata = { title: `Item details | Dashboard - ${CONFIG.appName}` };

export default function Page() {
  const { id = '' } = useParams();

  const { data, refetch: refetchItems } = useItemsQuery();

  const { data: senitronData, refetch: refetchSenitronItems } = useSenitronItemsQuery();

  const [items, setItems] = useState(null);

  const [senitronItems, setSenitronItems] = useState(null);

  const [currentItem, setCurrentItem] = useState(null);

  const [currentSenitronItem, setCurrentSenitronItem] = useState(null);

  useEffect(() => {
    if (data && data?.length) {
      setItems(data);
      setCurrentItem(data?.find((item) => item.itemId === id));
    }
    if (senitronData && senitronData?.length) {
      setSenitronItems(senitronData);
      setCurrentSenitronItem(senitronData?.find((item) => item.itemNumber === id));
    }
  }, [id, data, senitronData]);

  const baseWsUrl = `${CONFIG.websocketProtocol}://${CONFIG.apiHost}:${CONFIG.apiPort}/${CONFIG.apiDomain}/ws`;

  const onMessage = useCallback((m, _refetchFunc) => {
    if (['created', 'updated', 'deleted'].includes(m.type)) _refetchFunc?.();
  }, []);

  useWebsocket(`${baseWsUrl}/inventory_items/`, (msg) => onMessage(msg, refetchItems));
  useWebsocket(`${baseWsUrl}/senitron_inventory_items/`, (msg) => onMessage(msg, refetchSenitronItems));

  if (!currentItem && !currentSenitronItem) {
    return null;
  }

  return (
    <>
      <Helmet>
        <title> {metadata.title}</title>
      </Helmet>

      <ItemDetailsView item={currentItem} senitronItem={currentSenitronItem} setItem={setCurrentItem} setSenitronItem={setCurrentSenitronItem} />
    </>
  );
}
