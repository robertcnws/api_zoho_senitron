import { Helmet } from 'react-helmet-async';

import { CONFIG } from 'src/config-global';

import { ItemListView } from 'src/sections/item/view';

// ----------------------------------------------------------------------

const metadata = { title: `Item list | Dashboard - ${CONFIG.appName}` };

export default function Page() {
  return (
    <>
      <Helmet>
        <title> {metadata.title}</title>
      </Helmet>

      <ItemListView />
    </>
  );
}
