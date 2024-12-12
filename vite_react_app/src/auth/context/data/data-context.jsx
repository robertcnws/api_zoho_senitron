// src/contexts/DataContext.jsx

import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useItemsQuery, useSenitronItemsQuery } from 'src/_mock/_items';
import { useShipmentsQuery } from 'src/_mock/_shipment';
import { usePackagesQuery } from 'src/_mock/_package';
import { useSkuTrackInfoQuery } from 'src/_mock/_sku_track_info';
import { useItemAssetsTrackQuery } from 'src/_mock/_itemAssetsTrack';
import { useJobsUpdatingTimesQuery } from 'src/_mock/_jobsUpdatingTime';
import { useManualUpdatingJobsQuery } from 'src/_mock/_manualUpdatingJobs';
import { useTimelineItemsQuery } from 'src/_mock/_timelineItems';
import { useSenitronAssetsLogsQuery } from 'src/_mock/_itemAssetsLogs';
import { useNotificationsQuery } from 'src/_mock/_notification';

const DataContext = createContext();

export const useDataContext = () => useContext(DataContext);

export const DataProvider = ({ children }) => {

    const userLogged = useMemo(() => JSON.parse(localStorage.getItem('userLogged')), []);

    const [countLostItems, setCountLostItems] = useState(0);

    const { data: items, loading: loadingItems, error: errorItems } = useItemsQuery();
    const { data: senitronItems, loading: loadingSenitronItems, error: errorSenitronItems } = useSenitronItemsQuery();
    const { data: timelineItems, loading: loadingTimelineItems, error: errorTimelineItems } = useTimelineItemsQuery();
    const { data: itemsSkusTrack, loading: loadingItemsSkusTrack, error: errorItemsSkusTrack } = useSkuTrackInfoQuery();
    const { data: jobsUpdatingTime, loading: loadingJobsUpdatingTime, error: errorJobsUpdatingTime } = useJobsUpdatingTimesQuery();
    const { data: manualUpdatingJobs, loading: loadingManualUpdatingJobs, error: errorManualUpdatingJobs } = useManualUpdatingJobsQuery();
    const { data: shipments, loading: loadingShipments, error: errorShipments } = useShipmentsQuery(null, null);
    const { data: senitronAssetsLogs, loading: loadingSenitronAssetsLogs, error: errorSenitronAssetsLogs } = useSenitronAssetsLogsQuery(null);
    const { data: notifications, loading: loadingNotifications, error: errorNotifications } = useNotificationsQuery(userLogged?.data.username);

    const loading = loadingItems ||
        loadingSenitronItems ||
        loadingTimelineItems ||
        loadingItemsSkusTrack ||
        loadingJobsUpdatingTime ||
        loadingManualUpdatingJobs ||
        loadingShipments ||
        loadingSenitronAssetsLogs ||
        loadingNotifications;
    const error = errorItems ||
        errorSenitronItems ||
        errorTimelineItems ||
        errorItemsSkusTrack ||
        errorJobsUpdatingTime ||
        errorManualUpdatingJobs ||
        errorShipments ||
        errorSenitronAssetsLogs ||
        errorNotifications;


    // const [updatedNotifications, setUpdatedNotifications] = useState([]);


    // useEffect(() => {
        // const interval = setInterval(() => {
        //     setUpdatedNotifications(notifications);
        // }, 5000);
        // return () => clearInterval(interval);
    // }, [notifications]);


    const userNotifications = useMemo(() => notifications || null, [notifications]);

    const itemsZohoData = useMemo(() => items || null, [items]);

    const itemsTimelineData = useMemo(() => timelineItems || null, [timelineItems]);

    const itemsSkuTrackInfo = useMemo(() => itemsSkusTrack || null, [itemsSkusTrack]);

    const jobsUpdatingTimeData = useMemo(() => jobsUpdatingTime || null, [jobsUpdatingTime]);

    const manualUpdatingJobsData = useMemo(() => manualUpdatingJobs || null, [manualUpdatingJobs]);

    const itemsSenitronLogsInfo = useMemo(() => senitronAssetsLogs || null, [senitronAssetsLogs]);

    const itemsZohoSenitron = useMemo(() => {
        if (itemsZohoData && senitronItems) {
            const zohoSenitronItems = itemsZohoData.map((item) => {
                const senitronItem =
                    senitronItems.find(
                        (sItem) => String(sItem?.itemNumber) === String(item?.itemId)
                    ) || {};

                return {
                    ...item,
                    quantity: senitronItem.count || 0,
                    difference:
                        parseInt(senitronItem.count || '0', 10) -
                        parseInt(item.stockOnHand || '0', 10),
                    assets: senitronItem.assets || [],
                };
            });

            return sortBySku(zohoSenitronItems);
        }
        return null;
    }, [itemsZohoData, senitronItems]);


    const itemsSenitronZoho = useMemo(() => {
        if (itemsZohoData && senitronItems) {
            const senitronZohoItems = senitronItems.map((item) => {
                const zohoItem =
                    itemsZohoData.find(
                        (zItem) => String(zItem?.itemId) === String(item?.itemNumber)
                    ) || {};

                return {
                    ...item,
                    itemId: zohoItem.itemId || '',
                    sku: zohoItem.sku || '',
                    name: zohoItem.name || '',
                    stockOnHand: zohoItem.stockOnHand || 0,
                    quantity: item.count || 0,
                    syncedWithSenitron: zohoItem.syncedWithSenitron,
                    ignoreErrors: zohoItem.ignoreErrors,
                    difference:
                        parseInt(zohoItem.stockOnHand || '0', 10) -
                        parseInt(item.count || '0', 10),
                };
            });
            return sortBySku(senitronZohoItems);
        }
        return null;
    }, [itemsZohoData, senitronItems]);


    const allShipments = useMemo(() => shipments || null, [shipments]);

    // console.log('allShipments', allShipments);

    const allPackages = useMemo(() => {
        if (allShipments) {
            const packages = [];
            allShipments.forEach(shipment => {
                const parsedPackage = parsePackages(shipment.packages, shipment.date);
                packages.push(parsedPackage);
            });
            return packages;
        }
        return null;
    }, [allShipments]);

    const { data: linePackages } = usePackagesQuery(null, null, allPackages?.flatMap(pkgs => pkgs.map(pkg => pkg.package_id)));

    const allLinePackages = useMemo(() => linePackages || null, [linePackages]);

    const dataItems = useMemo(() => {
        if (linePackages) {
            const itemsPacks = linePackages?.map(pkg => ({
                packageId: pkg.packageId,
                packageNumber: pkg.packageNumber,
                shipmentId: pkg.shipmentId,
                shipmentNumber: pkg.shipmentNumber,
                totalQuantity: pkg.totalQuantity,
                date: pkg.date,
                items: parseLineItems(pkg.lineItems) || [],
            }));
            return itemsPacks;
        }
        return [];
    }, [linePackages]);


    const mergeItems = useMemo(() => {
        if (allShipments && allPackages && allLinePackages && dataItems) {
            const merged = dataItems.flatMap(itemList =>
                itemList.items.map(item => ({
                    itemId: item.item_id,
                    sku: item.sku,
                    name: item.name,
                    quantity: item.quantity,
                    shipmentId: itemList.shipmentId,
                    shipmentNumber: itemList.shipmentNumber,
                    packageId: itemList.packageId,
                    packageNumber: itemList.packageNumber,
                    date: itemList.date,
                }))
            );
            return merged;
        }
        return [];
    }, [allShipments, allPackages, allLinePackages, dataItems]);

    const groupedItems = mergeItems.reduce((acc, currentItem) => {
        const { itemId, name, sku, packageId, quantity, shipmentId, shipmentNumber, packageNumber, date } = currentItem;
        const key = `${itemId}-${date}`;
        if (!acc[key]) {
            acc[key] = {
                itemId,
                name,
                sku,
                date,
                itemTotalQty: 0,
                linePackages: []
            };
        }
        acc[key].itemTotalQty += quantity;
        acc[key].linePackages.push({
            packageId,
            packageNumber,
            quantity,
            shipmentId,
            shipmentNumber
        });
        return acc;
    }, {});

    const finalGroupedArray = useMemo(() => Object.values(groupedItems), [groupedItems]);


    // Logs
    const logs = itemsSenitronLogsInfo?.flatMap(group => group.logs.map(log => ({
        ...log,
        itemNumber: group.itemNumber,
        date: group.date,
    })));

    const syncedItemIds = new Set(
        itemsZohoSenitron
            ?.filter(item => item.syncedWithSenitron === true)
            .map(item => item.itemId)
    );

    const itemsMap = new Map(itemsZohoSenitron?.map(item => [item.itemId, item]));

    const filteredLogs = logs
        ?.filter(log => syncedItemIds.has(log.itemNumber))
        ?.map(log => {
            const matchedItem = itemsMap.get(log.itemNumber);
            return {
                ...log,
                sku: matchedItem?.sku
            };
        });

    const objectsGroupedLogs = useMemo(() => {
        const groupedLogs = {};

        filteredLogs?.forEach(log => {
            const itemNumber = log.itemNumber;
            const date = log.date;
            const sku = log.sku;
            const groupKey = `${itemNumber}-${date}`;

            if (!groupedLogs[groupKey]) {
                groupedLogs[groupKey] = {
                    itemNumber,
                    sku,
                    date,
                    logs: [],
                };
            }

            groupedLogs[groupKey].logs.push(log);
        });

        return Object.values(groupedLogs);
    }, [filteredLogs]);


    const itemsAssetsLogsInfo = useMemo(() =>
        objectsGroupedLogs?.map(group => {
            const liveLogs = group.logs.filter(
                log => log.currentStatusName && log.currentStatusName.toLowerCase().includes('live') && !log.lastStatusName.toLowerCase().includes('live')
            );
            const killedLogs = group.logs.filter(
                log => log.currentStatusName && log.currentStatusName.toLowerCase().includes('kill') && !log.lastStatusName.toLowerCase().includes('kill')
            );
            const removedLogs = group.logs.filter(
                log => log.currentStatusName && log.currentStatusName.toLowerCase().includes('removed') && !log.lastStatusName.toLowerCase().includes('removed')
            );

            const liveLogsSet = [...new Set(liveLogs.map(log => log.serialNumber))].sort();
            const killedLogsSet = [...new Set(killedLogs.map(log => log.serialNumber))].sort();
            const removedLogsSet = [...new Set(removedLogs.map(log => log.serialNumber))].sort();

            const uniqueLiveCount = liveLogsSet.length;
            const uniqueKilledCount = killedLogsSet.length;
            const uniqueRemovedCount = removedLogsSet.length;

            if (uniqueLiveCount === 0 && uniqueKilledCount === 0 && uniqueRemovedCount === 0) {
                return null;
            }

            return {
                itemNumber: group.itemNumber,
                sku: group.sku,
                date: group.date,
                totalLive: uniqueLiveCount,
                totalKilled: uniqueKilledCount,
                totalRemoved: uniqueRemovedCount,
                liveLogsSet,
                killedLogsSet,
                removedLogsSet,
                logs: group.logs,
            };
        })
        , [objectsGroupedLogs]);






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
            setCountLostItems,
        ]
    );

    return (
        <DataContext.Provider value={value}>
            {children}
        </DataContext.Provider>
    );
};

function sortBySku(items) {
    return items.sort((a, b) => {
        const skuA = a.sku || '';
        const skuB = b.sku || '';

        const isSkuAEmpty = !skuA.trim();
        const isSkuBEmpty = !skuB.trim();

        return isSkuAEmpty && !isSkuBEmpty ? 1 : !isSkuAEmpty && isSkuBEmpty ? -1 : isSkuAEmpty && isSkuBEmpty ? 0 : skuA.localeCompare(skuB);

    });
}

const parseLineItems = (lineItems) => {
    if (typeof lineItems === 'string') {
        try {
            return JSON.parse(lineItems).filter(item => item.sku);
        } catch (err) {
            console.error('Error al parsear lineItems:', err);
            return [];
        }
    } else {
        return (lineItems || []).filter(item => item.sku);
    }
}

const parsePackages = (packages, date = null) => {
    if (typeof packages === 'string') {
        try {
            const parsedPackages = JSON.parse(packages)
                .filter(pkg => pkg.package_id)
                .map(pkg => ({ ...pkg, date }));
            return parsedPackages;
        } catch (err) {
            console.error('Error al parsear packages:', err);
            return [];
        }
    } else {
        return (packages || []).filter(pkg => pkg.package_id).map(pkg => ({ ...pkg, date }));
    }
};
