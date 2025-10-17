import { fDate } from "./format-time";

export const handleShippedSerialQuantity = (itemShipped) => itemShipped?.logs.reduce(
    (acc, h) => acc + ((h.currentStatusName.toLowerCase().includes('removed') || h.currentStatusName.toLowerCase().includes('kill')) ? 1 : 0), 0
);

export const countingLostItems = (itemsZohoSenitron, listSerials, listShipments, endDate) => {
    if (itemsZohoSenitron && itemsZohoSenitron.length > 0 && 
        listSerials && listSerials.length > 0 && 
        listShipments && listShipments.length > 0
    ) {

        const allowedIds = itemsZohoSenitron?.filter((item) => item.syncedWithSenitron).map((item) => item.itemId);

        const allowedIdsSet = new Set(allowedIds);

        const syncedShipments = listShipments?.filter(item => allowedIdsSet.has(item.itemId));

        const rData = syncedShipments?.map((item) => {
            const senitronItem = listSerials?.find((sItem) => sItem?.itemNumber === item.itemId);
            return {
                ...item,
                shippedSerialsQuantity: handleShippedSerialQuantity(senitronItem) || 0,
                differenceShipped: handleShippedSerialQuantity(senitronItem) ?
                    (item.itemTotalQty - handleShippedSerialQuantity(senitronItem)) : item.itemTotalQty,
                receivedSerialsQuantity: senitronItem?.logs.reduce(
                    (acc, h) => acc + (h.currentStatusName.toLowerCase().includes('live') ? 1 : 0), 0
                ) || 0,
                isReconciled: false,
                logs: senitronItem?.logs,
            };
        });

        const rDataZohoSenitron = rData?.map((item) => {
            const senitronItem = itemsZohoSenitron?.find((sItem) => sItem?.itemId === item.itemId);
            return {
                ...item,
                isReconciled: Number.parseInt(senitronItem?.stockOnHand, 10) - Number.parseInt(senitronItem?.quantity, 10) === 0 || false,
            }

        });

        const existingItemIds = new Set(rDataZohoSenitron.map(item => item.itemId));

        const newItems = listSerials
            .filter(item => !existingItemIds.has(item.itemNumber))
            .map(item => ({
                ...item,
                itemId: item.itemNumber,
                itemTotalQty: 0,
                shippedSerialsQuantity: handleShippedSerialQuantity(item) || 0,
                differenceShipped: handleShippedSerialQuantity(item) ?
                    (0 - handleShippedSerialQuantity(item)) : 0,
                receivedSerialsQuantity: item?.logs.reduce(
                    (acc, h) => acc + (h.currentStatusName.toLowerCase().includes('live') ? 1 : 0), 0
                ) || 0,
            }));


        const updatedRDataZohoSenitron = [...rDataZohoSenitron, ...newItems];



        const filteredData = updatedRDataZohoSenitron?.map(item => {

            const filteredLogs = item.logs?.filter(log => fDate(log.createdAt, 'YYYY-MM-DD') === fDate(endDate, 'YYYY-MM-DD'));
            return {
                ...item,
                logs: filteredLogs,
            };
        });

        const finalFilteredData = filteredData?.map((item) => {
            const senitronItem = itemsZohoSenitron?.find((sItem) => sItem?.itemId === item.itemId);
            return {
                ...item,
                isReconciled: Number.parseInt(senitronItem?.stockOnHand, 10) - Number.parseInt(senitronItem?.quantity, 10) === 0 || false,
            }

        });

        const lostCount = finalFilteredData.filter(
            (it) => it.differenceShipped < 0 && !it.isReconciled && it.date === fDate(endDate, 'YYYY-MM-DD')
        ).length;

        if (lostCount > 0 && fDate(endDate, 'YYYY-MM-DD') === fDate(new Date(), 'YYYY-MM-DD')) {
            return {
                lostCount,
                finalFilteredData
            }
        }
        return { lostCount: 0, finalFilteredData };

    }
    return { lostCount: 0, finalFilteredData: [] };
}