import { Helmet } from 'react-helmet-async';
import { DataProvider } from 'src/auth/context/data/data-context';

import { CONFIG } from 'src/config-global';

import { LiveMonitorAnalyticsView } from 'src/sections/live-monitor/view';

// ----------------------------------------------------------------------

const metadata = { title: `Analytics | Dashboard - ${CONFIG.appName}` };

export default function Page() {
  return (
    <>
      <Helmet>
        <title> {metadata.title}</title>
      </Helmet>

      <DataProvider>
        <LiveMonitorAnalyticsView />
      </DataProvider>
    </>
  );
}
