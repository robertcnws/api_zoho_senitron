import { jsPDF as JsPDF } from 'jspdf';
import 'jspdf-autotable';
import logoBase64 from '../../public/logo/logo-red.png'; 

export const generatePrintablePDF = ({ data, title }) => {
    const doc = new JsPDF('p', 'pt', 'a4'); 

    const margin = 40;
    const logoWidth = 50;
    const logoHeight = 50;
    
    doc.addImage(logoBase64, 'PNG', margin, margin, logoWidth, logoHeight);
    
    doc.setFontSize(11);
    doc.text(title, margin + logoWidth + 10, margin + 30);
    
    const date = new Date().toLocaleDateString();
    doc.setFontSize(10);
    doc.text(`Fecha: ${date}`, doc.internal.pageSize.getWidth() - margin - 100, margin + 30);
    
    const columns = [
        { dataKey: 'index', header: '#' },
        { dataKey: 'sku', header: 'SKU' },
        { dataKey: 'stockOnHand', header: 'On Hand' },
        { dataKey: 'quantity', header: 'RFID Count' },
        { dataKey: 'difference', header: 'Difference' },
    ];
    
    const rows = data.map((item, index) => ({
        index: index + 1,
        sku: item.sku,
        stockOnHand: item.stockOnHand,
        quantity: item.quantity,
        difference: item.difference,
    }));

    doc.autoTable({
        columns,
        body: rows,
        startY: margin + logoHeight + 40, 
        margin: { horizontal: margin },
        styles: { fontSize: 12 },
        headStyles: { fillColor: [22, 160, 133] }, 
        theme: 'striped', 
        didDrawPage: (items) => {
            const pageCount = doc.internal.getNumberOfPages();
            doc.setFontSize(10);
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            doc.text(`Page ${doc.internal.getCurrentPageInfo().pageNumber} of ${pageCount}`, pageWidth / 2, pageHeight - margin / 2, { align: 'center' });
            doc.text('© 2024 NWS. Warehouse Management System. All rights reserved.', pageWidth / 2, pageHeight - margin / 2 + 10, { align: 'center' });
        },
    });

    const pdfBlob = doc.output('blob');
    
    const blobUrl = URL.createObjectURL(pdfBlob);
    
    window.open(blobUrl, '_blank');

    setTimeout(() => {
        URL.revokeObjectURL(blobUrl);
    }, 1000);
};
