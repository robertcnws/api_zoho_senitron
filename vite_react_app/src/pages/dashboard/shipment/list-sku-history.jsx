import { Helmet } from 'react-helmet-async';

import { CONFIG } from 'src/config-global';

import { ShipmentListSkuHistoryView } from 'src/sections/shipment/view/shipment-list-sku-history-view';

// ----------------------------------------------------------------------

const metadata = { title: `SKU's History | Dashboard - ${CONFIG.appName}` };

export default function Page() {
  return (
    <>
      <Helmet>
        <title> {metadata.title}</title>
      </Helmet>

      <ShipmentListSkuHistoryView />
    </>
  );
}
