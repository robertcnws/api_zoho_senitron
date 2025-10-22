// src/contexts/DataContext.jsx
import React, {
  useMemo,
  useState,
  useContext,
  useCallback,
  useRef,
  createContext,
} from 'react';

import { useWebsocket } from 'src/hooks/use-websocket';
import { fDate } from 'src/utils/format-time';
import { CONFIG } from 'src/config-global';

import { usePackagesQuery } from 'src/_mock/_package';
import { useShipmentsQuery } from 'src/_mock/_shipment';
import { useNotificationsQuery } from 'src/_mock/_notification';
import { useSkuTrackInfoQuery } from 'src/_mock/_sku_track_info';
import { useTimelineItemsQuery } from 'src/_mock/_timelineItems';
import { useSenitronAssetsLogsQuery } from 'src/_mock/_itemAssetsLogs';
import { useItemsQuery, useSenitronItemsQuery } from 'src/_mock/_items';
import { useJobsUpdatingTimesQuery } from 'src/_mock/_jobsUpdatingTime';
import { useManualUpdatingJobsQuery } from 'src/_mock/_manualUpdatingJobs';

const DataContext = createContext();
export const useDataContext = () => useContext(DataContext);

// ---------- utils locales
const collator = new Intl.Collator(undefined, { sensitivity: 'base', numeric: true });

function sortBySku(items) {
  // muta el array recibido, pero siempre se llama sobre arrays nuevos
  return items.sort((a, b) => {
    const skuA = a.sku || '';
    const skuB = b.sku || '';
    const isSkuAEmpty = !skuA.trim();
    const isSkuBEmpty = !skuB.trim();
    if (isSkuAEmpty && !isSkuBEmpty) return 1;
    if (!isSkuAEmpty && isSkuBEmpty) return -1;
    if (isSkuAEmpty && isSkuBEmpty) return 0;
    return collator.compare(skuA, skuB);
  });
}

function safeJSONParse(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

function parseLineItems(lineItems) {
  const raw = typeof lineItems === 'string' ? safeJSONParse(lineItems) : lineItems;
  if (!raw) return [];
  return (Array.isArray(raw) ? raw : []).filter((it) => it && it.sku);
}

function parsePackages(packages, date = null) {
  const raw = typeof packages === 'string' ? safeJSONParse(packages) : packages;
  if (!raw) return [];
  return (Array.isArray(raw) ? raw : [])
    .filter((pkg) => pkg?.package_id)
    .map((pkg) => ({ ...pkg, date }));
}

// Debounce “por canal” para refetch vía WS
function useDebouncedRefetch() {
  const timersRef = useRef(new Map());
  return useCallback((key, fn, wait = 300) => {
    const timers = timersRef.current;
    const prev = timers.get(key);
    if (prev) clearTimeout(prev);
    const t = setTimeout(() => {
      timers.delete(key);
      if (typeof fn === 'function') fn();
    }, wait);
    timers.set(key, t);
  }, []);
}

export const DataProvider = ({ children }) => {
  const userLogged = useMemo(
    () => JSON.parse(localStorage.getItem('userLogged')),
    []
  );

  const [countLostItems, setCountLostItems] = useState(0);

  // === Queries base ===
  const {
    data: items,
    loading: loadingItems,
    error: errorItems,
    refetch: refetchItems,
  } = useItemsQuery();

  const {
    data: senitronItems,
    loading: loadingSenitronItems,
    error: errorSenitronItems,
    refetch: refetchSenitronItems,
  } = useSenitronItemsQuery();

  const {
    data: timelineItems,
    loading: loadingTimelineItems,
    error: errorTimelineItems,
    refetch: refetchTimelineItems,
  } = useTimelineItemsQuery();

  const {
    data: itemsSkusTrack,
    loading: loadingItemsSkusTrack,
    error: errorItemsSkusTrack,
    refetch: refetchItemsSkusTrack,
  } = useSkuTrackInfoQuery();

  const {
    data: jobsUpdatingTime,
    loading: loadingJobsUpdatingTime,
    error: errorJobsUpdatingTime,
    refetch: refetchJobsUpdatingTime,
  } = useJobsUpdatingTimesQuery();

  const {
    data: manualUpdatingJobs,
    loading: loadingManualUpdatingJobs,
    error: errorManualUpdatingJobs,
    refetch: refetchManualUpdatingJobs,
  } = useManualUpdatingJobsQuery();

  const {
    data: shipments,
    loading: loadingShipments,
    error: errorShipments,
    refetch: refetchShipments,
  } = useShipmentsQuery(null, null);

  const {
    data: senitronAssetsLogs,
    loading: loadingSenitronAssetsLogs,
    error: errorSenitronAssetsLogs,
    refetch: refetchSenitronAssetsLogs,
  } = useSenitronAssetsLogsQuery(null);

  const {
    data: notifications,
    loading: loadingNotifications,
    error: errorNotifications,
    refetch: refetchNotifications,
  } = useNotificationsQuery(userLogged?.data.username);

  // === WS con debounce por canal ===
  const baseWsUrl = `${CONFIG.websocketProtocol}://${CONFIG.apiHost}:${CONFIG.apiPort}/${CONFIG.apiDomain}/ws`;
  const debouncedRefetch = useDebouncedRefetch();

  const onMessage = useCallback(
    (m, key, refetch) => {
      if (m && ['created', 'updated', 'deleted'].includes(m.type)) {
        debouncedRefetch(key, refetch, 300);
      }
    },
    [debouncedRefetch]
  );

  useWebsocket(`${baseWsUrl}/inventory_items/`, (msg) =>
    onMessage(msg, 'inventory_items', refetchItems)
  );
  useWebsocket(`${baseWsUrl}/senitron_inventory_items/`, (msg) =>
    onMessage(msg, 'senitron_inventory_items', refetchSenitronItems)
  );
  useWebsocket(`${baseWsUrl}/senitron_timelines/`, (msg) =>
    onMessage(msg, 'senitron_timelines', refetchTimelineItems)
  );
  useWebsocket(`${baseWsUrl}/sku_track_info/`, (msg) =>
    onMessage(msg, 'sku_track_info', refetchItemsSkusTrack)
  );
  useWebsocket(`${baseWsUrl}/jobs_updating_times/`, (msg) =>
    onMessage(msg, 'jobs_updating_times', refetchJobsUpdatingTime)
  );
  useWebsocket(`${baseWsUrl}/manual_updating_jobs/`, (msg) =>
    onMessage(msg, 'manual_updating_jobs', refetchManualUpdatingJobs)
  );
  useWebsocket(`${baseWsUrl}/shipment_orders/`, (msg) =>
    onMessage(msg, 'shipment_orders', refetchShipments)
  );
  useWebsocket(`${baseWsUrl}/senitron_inventory_items_asset_logs/`, (msg) =>
    onMessage(msg, 'senitron_inventory_items_asset_logs', refetchSenitronAssetsLogs)
  );
  useWebsocket(`${baseWsUrl}/notification_users/`, (msg) =>
    onMessage(msg, 'notification_users', refetchNotifications)
  );

  // === Flags globales ===
  const loading =
    loadingItems ||
    loadingSenitronItems ||
    loadingTimelineItems ||
    loadingItemsSkusTrack ||
    loadingJobsUpdatingTime ||
    loadingManualUpdatingJobs ||
    loadingShipments ||
    loadingSenitronAssetsLogs ||
    loadingNotifications;

  const error =
    errorItems ||
    errorSenitronItems ||
    errorTimelineItems ||
    errorItemsSkusTrack ||
    errorJobsUpdatingTime ||
    errorManualUpdatingJobs ||
    errorShipments ||
    errorSenitronAssetsLogs ||
    errorNotifications;

  // === Memo de datos base (evita re-render si no cambian) ===
  const userNotifications = useMemo(() => notifications ?? null, [notifications]);
  const itemsZohoData = useMemo(() => items ?? null, [items]);
  const itemsTimelineData = useMemo(() => timelineItems ?? null, [timelineItems]);
  const itemsSkuTrackInfo = useMemo(() => itemsSkusTrack ?? null, [itemsSkusTrack]);
  const jobsUpdatingTimeData = useMemo(() => jobsUpdatingTime ?? null, [jobsUpdatingTime]);
  const manualUpdatingJobsData = useMemo(() => manualUpdatingJobs ?? null, [manualUpdatingJobs]);
  const itemsSenitronLogsInfo = useMemo(() => senitronAssetsLogs ?? null, [senitronAssetsLogs]);

  // === Joins Zoho <-> Senitron en O(n) con maps (sin for...of) ===
  const { itemsZohoSenitron, itemsSenitronZoho } = useMemo(() => {
    if (!itemsZohoData || !senitronItems)
      return { itemsZohoSenitron: null, itemsSenitronZoho: null };

    const senByNum = new Map(
      senitronItems.map((s) => [String(s?.itemNumber), s])
    );
    const zohoById = new Map(itemsZohoData.map((z) => [String(z?.itemId), z]));

    const zs = sortBySku(
      itemsZohoData.map((z) => {
        const s = senByNum.get(String(z?.itemId)) || {};
        const stock = parseInt(z?.stockOnHand ?? '0', 10);
        const qty = parseInt(s?.count ?? '0', 10);
        return {
          ...z,
          quantity: qty,
          difference: qty - stock,
          assets: s.assets || [],
        };
      })
    );

    const sz = sortBySku(
      senitronItems.map((s) => {
        const z = zohoById.get(String(s?.itemNumber)) || {};
        const stock = parseInt(z?.stockOnHand ?? '0', 10);
        const qty = parseInt(s?.count ?? '0', 10);
        return {
          ...s,
          itemId: z.itemId || '',
          sku: z.sku || '',
          name: z.name || '',
          stockOnHand: z.stockOnHand || 0,
          quantity: s.count || 0,
          syncedWithSenitron: z.syncedWithSenitron,
          ignoreErrors: z.ignoreErrors,
          difference: stock - qty,
        };
      })
    );

    return { itemsZohoSenitron: zs, itemsSenitronZoho: sz };
  }, [itemsZohoData, senitronItems]);

  // === Shipments / Packages ===
  const allShipments = useMemo(() => shipments ?? null, [shipments]);

  const allPackages = useMemo(() => {
    if (!allShipments?.length) return null;
    return allShipments.map((sh) => parsePackages(sh.packages, sh.date));
  }, [allShipments]);

  const packageIds = useMemo(() => {
    if (!allPackages) return null;
    const ids = allPackages.flatMap((group) => group.map((p) => p.package_id));
    return ids.length ? ids : null;
  }, [allPackages]);

  const { data: linePackages } = usePackagesQuery(null, null, packageIds ?? undefined);

  const allLinePackages = useMemo(() => linePackages ?? null, [linePackages]);

  // === Normalización de linePackages ===
  const dataItems = useMemo(() => {
    if (!linePackages?.length) return [];
    return linePackages.map((pkg) => ({
      packageId: pkg.packageId,
      packageNumber: pkg.packageNumber,
      shipmentId: pkg.shipmentId,
      shipmentNumber: pkg.shipmentNumber,
      totalQuantity: pkg.totalQuantity,
      date: pkg.date,
      items: parseLineItems(pkg.lineItems),
    }));
  }, [linePackages]);

  // === Merge y agrupación (reduce + forEach, sin continue) ===
  const finalGroupedArray = useMemo(() => {
    if (!allShipments || !allPackages || !allLinePackages || !dataItems.length) return [];
    const map = dataItems.reduce((acc, list) => {
      const { date, items: li } = list;
      if (!li?.length) return acc;
      li.forEach((it) => {
        const key = `${it.item_id}-${date}`;
        let node = acc.get(key);
        if (!node) {
          node = {
            itemId: it.item_id,
            name: it.name,
            sku: it.sku,
            date,
            itemTotalQty: 0,
            linePackages: [],
          };
          acc.set(key, node);
        }
        node.itemTotalQty += it.quantity;
        node.linePackages.push({
          packageId: list.packageId,
          packageNumber: list.packageNumber,
          quantity: it.quantity,
          shipmentId: list.shipmentId,
          shipmentNumber: list.shipmentNumber,
        });
      });
      return acc;
    }, new Map());
    return Array.from(map.values());
  }, [allShipments, allPackages, allLinePackages, dataItems]);

  // === Logs Senitron (sin for...of, sin continue) ===
  const itemsAssetsLogsInfo = useMemo(() => {
    if (!itemsSenitronLogsInfo?.length || !itemsZohoSenitron?.length) return [];

    const syncedItemIds = new Set(
      itemsZohoSenitron
        .filter((it) => it.syncedWithSenitron === true)
        .map((it) => it.itemId)
    );
    const itemsById = new Map(itemsZohoSenitron.map((it) => [it.itemId, it]));

    const flat = itemsSenitronLogsInfo
      .filter((group) => syncedItemIds.has(group.itemNumber))
      .flatMap((group) => {
        const sku = itemsById.get(group.itemNumber)?.sku;
        const date = group.date;
        return group.logs.map((log) => ({ ...log, itemNumber: group.itemNumber, sku, date }));
      });

    // Agrupar por (itemNumber-date)
    const groups = flat.reduce((acc, log) => {
      const key = `${log.itemNumber}-${log.date}`;
      const g = acc.get(key) || { itemNumber: log.itemNumber, sku: log.sku, date: log.date, logs: [] };
      g.logs.push(log);
      acc.set(key, g);
      return acc;
    }, new Map());

    const out = [];
    groups.forEach((g) => {
      const dayStr = String(g.date);
      const live = new Set();
      const killed = new Set();
      const removed = new Set();
      const seen = new Set();

      g.logs.forEach((log) => {
        const k = `${log.serialNumber}-${log.currentStatusId}-${log.lastStatusId}-${log.createdAt}`;
        if (seen.has(k)) return;
        seen.add(k);

        const createdDay = log.createdAt && fDate(log.createdAt, 'YYYY-MM-DD');
        if (createdDay !== dayStr) return;

        const cur = (log.currentStatusName || '').toLowerCase();
        const last = (log.lastStatusName || '').toLowerCase();

        if (cur.includes('live') && !last.includes('live')) {
          live.add(log.serialNumber);
        } else if (cur.includes('kill') && !last.includes('kill')) {
          killed.add(log.serialNumber);
        } else if (cur.includes('removed') && !last.includes('removed')) {
          removed.add(log.serialNumber);
        }
      });

      const liveLogsSet = Array.from(live).sort(collator.compare);
      const killedLogsSet = Array.from(killed).sort(collator.compare);
      const removedLogsSet = Array.from(removed).sort(collator.compare);

      if (!liveLogsSet.length && !killedLogsSet.length && !removedLogsSet.length) return;

      out.push({
        itemNumber: g.itemNumber,
        sku: g.sku,
        date: g.date,
        totalLive: liveLogsSet.length,
        totalKilled: killedLogsSet.length,
        totalRemoved: removedLogsSet.length,
        liveLogsSet,
        killedLogsSet,
        removedLogsSet,
        logs: g.logs,
      });
    });

    return out;
  }, [itemsSenitronLogsInfo, itemsZohoSenitron]);

  // === Context value memorizado ===
  const value = useMemo(
    () => ({
      userNotifications,
      items,
      senitronItems,
      timelineItems,
      itemsSkusTrack,
      jobsUpdatingTime,
      manualUpdatingJobs,
      loading,
      error,

      itemsZohoData,
      itemsTimelineData,
      itemsSkuTrackInfo,
      jobsUpdatingTimeData,
      manualUpdatingJobsData,

      itemsAssetsLogsInfo,
      itemsZohoSenitron,
      itemsSenitronZoho,
      finalGroupedArray,

      countLostItems,
      setCountLostItems,

      refetchItems,
      refetchSenitronItems,
      refetchTimelineItems,
      refetchItemsSkusTrack,
      refetchJobsUpdatingTime,
      refetchManualUpdatingJobs,
      refetchShipments,
      refetchSenitronAssetsLogs,
      refetchNotifications,
    }),
    [
      userNotifications,
      items,
      senitronItems,
      timelineItems,
      itemsSkusTrack,
      jobsUpdatingTime,
      manualUpdatingJobs,
      loading,
      error,
      itemsZohoData,
      itemsTimelineData,
      itemsSkuTrackInfo,
      jobsUpdatingTimeData,
      manualUpdatingJobsData,
      itemsAssetsLogsInfo,
      itemsZohoSenitron,
      itemsSenitronZoho,
      finalGroupedArray,
      countLostItems,
      refetchItems,
      refetchSenitronItems,
      refetchTimelineItems,
      refetchItemsSkusTrack,
      refetchJobsUpdatingTime,
      refetchManualUpdatingJobs,
      refetchShipments,
      refetchSenitronAssetsLogs,
      refetchNotifications,
    ]
  );

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};
