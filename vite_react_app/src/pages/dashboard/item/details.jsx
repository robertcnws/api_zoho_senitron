import React, { useEffect, useState } from 'react';

import { Helmet } from 'react-helmet-async';

import { useParams } from 'src/routes/hooks';

import { useItemsQuery } from 'src/_mock/_items';
import { CONFIG } from 'src/config-global';

import { ItemDetailsView } from 'src/sections/item/view';

// ----------------------------------------------------------------------

const metadata = { title: `Item details | Dashboard - ${CONFIG.appName}` };

export default function Page() {
  const { id = '' } = useParams();

  const { data } = useItemsQuery();

  const [items, setItems] = useState(null);

  const [currentItem, setCurrentItem] = useState(null);

  useEffect(() => {
    if (data) {
      setItems(data);
      setCurrentItem(data.find((item) => item.itemId === id));
    }
  }, [id, data]);

  if (!currentItem) {
    return null;
  }
  
  return (
    <>
      <Helmet>
        <title> {metadata.title}</title>
      </Helmet>

      <ItemDetailsView item={currentItem} />
    </>
  );
}
