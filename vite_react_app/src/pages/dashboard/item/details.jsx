import { Helmet } from 'react-helmet-async';
import React, { useState, useEffect } from 'react';

import { useParams } from 'src/routes/hooks';

import { CONFIG } from 'src/config-global';
import { useItemsQuery, useSenitronItemsQuery } from 'src/_mock/_items';

import { ItemDetailsView } from 'src/sections/item/view';

// ----------------------------------------------------------------------

const metadata = { title: `Item details | Dashboard - ${CONFIG.appName}` };

export default function Page() {
  const { id = '' } = useParams();

  const { data } = useItemsQuery();

  const { data: senitronData } = useSenitronItemsQuery();

  const [items, setItems] = useState(null);

  const [senitronItems, setSenitronItems] = useState(null);

  const [currentItem, setCurrentItem] = useState(null);

  const [currentSenitronItem, setCurrentSenitronItem] = useState(null);

  useEffect(() => {
    if (data) {
      setItems(data);
      setCurrentItem(data.find((item) => item.itemId === id));
    }
    if (senitronData) {
      setSenitronItems(senitronData);
      setCurrentSenitronItem(senitronData.find((item) => item.itemNumber === id));
    }
  }, [id, data, senitronData]);

  if (!currentItem && !currentSenitronItem) {
    return null;
  }
  
  return (
    <>
      <Helmet>
        <title> {metadata.title}</title>
      </Helmet>

      <ItemDetailsView item={currentItem} senitronItem={currentSenitronItem} setItem={setCurrentItem} setSenitronItem={setCurrentSenitronItem}/>
    </>
  );
}
