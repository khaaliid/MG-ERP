/**
 * Receipt Printer Utility
 * Common utility for printing thermal receipts across the application
 */

interface ReceiptSettings {
  currencyCode: string;
  currencySymbol: string;
  receiptHeader: string;
  receiptFooter: string;
  businessName: string;
  businessAddress: string;
  businessPhone: string;
  businessEmail: string;
}

interface ReceiptItem {
  name: string;
  qty: number;
  price: number;
  size?: string | null;
  total: number;
}

interface ReceiptData {
  saleNumber: string;
  date: Date;
  cashier?: string;
  customerName?: string;
  items: ReceiptItem[];
  subtotal: number;
  discount: number;
  tax: number;
  taxRate?: number;
  total: number;
  paymentMethod: string;
  tenderedAmount?: number;
  changeAmount?: number;
}

function formatCurrency(v: number, currencyCode: string): string {
  const value = typeof v === 'number' && !isNaN(v) ? v : 0;
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currencyCode || 'USD' }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currencyCode || 'USD'}`;
  }
}

export function printReceipt(receiptData: ReceiptData, settings: ReceiptSettings): void {
  const {
    saleNumber,
    date,
    cashier,
    customerName,
    items,
    subtotal,
    discount,
    tax,
    taxRate,
    total,
    paymentMethod,
    tenderedAmount,
    changeAmount
  } = receiptData;

  const {
    currencyCode,
    receiptHeader,
    receiptFooter,
    businessName,
    businessAddress,
    businessPhone,
    businessEmail
  } = settings;

  const html = `<!DOCTYPE html>
  <html>
    <head>
      <meta charset="utf-8" />
      <title>Receipt - ${saleNumber}</title>
      <style>
        @page {
          size: 80mm auto;
          margin: 0;
        }
        @media print {
          body {
            width: 80mm;
            margin: 0;
            padding: 2mm;
          }
          @page {
            margin: 0;
          }
        }
        body { 
          font-family: 'Courier New', monospace; 
          width: 80mm; 
          margin: 0;
          padding: 2mm;
          font-size: 11px;
        }
        .center { text-align: center; }
        .small { font-size: 10px; color: #000; }
        .bold { font-weight: bold; }
        .divider { border-top: 1px dashed #000; margin: 6px 0; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        td { padding: 2px 0; }
        .totals td { padding: 4px 0; }
      </style>
    </head>
    <body>
      <div class="center">
        <div class="bold">${businessName || 'Store'}</div>
        ${businessAddress ? `<div class="small">${businessAddress}</div>` : ''}
        ${businessPhone ? `<div class="small">Tel: ${businessPhone}</div>` : ''}
        ${businessEmail ? `<div class="small">${businessEmail}</div>` : ''}
      </div>
      ${receiptHeader ? `<div class="divider"></div><div class="small center">${receiptHeader}</div>` : ''}
      <div class="divider"></div>
      <div class="small">Sale #: ${saleNumber}</div>
      <div class="small">Date: ${date.toLocaleString()}</div>
      ${cashier ? `<div class="small">Cashier: ${cashier}</div>` : ''}
      ${customerName ? `<div class="small">Customer: ${customerName}</div>` : ''}
      <div class="divider"></div>
      <table>
        ${items.map(item => `
          <tr>
            <td>${item.name}${item.size ? ' (' + item.size + ')' : ''}</td>
            <td class="small" style="text-align:right">${item.qty} x ${formatCurrency(item.price, currencyCode)}</td>
          </tr>
          <tr>
            <td></td>
            <td style="text-align:right" class="bold">${formatCurrency(item.total, currencyCode)}</td>
          </tr>
        `).join('')}
      </table>
      <div class="divider"></div>
      <table class="totals">
        <tr>
          <td>Subtotal</td>
          <td style="text-align:right">${formatCurrency(subtotal, currencyCode)}</td>
        </tr>
        ${discount > 0 ? `
        <tr>
          <td>Discount</td>
          <td style="text-align:right">${formatCurrency(discount, currencyCode)}</td>
        </tr>` : ''}
        <tr>
          <td>Tax${taxRate ? ' (' + Math.round(taxRate * 100) + '%)' : ''}</td>
          <td style="text-align:right">${formatCurrency(tax, currencyCode)}</td>
        </tr>
        <tr>
          <td class="bold">Total</td>
          <td style="text-align:right" class="bold">${formatCurrency(total, currencyCode)}</td>
        </tr>
        <tr>
          <td>Method</td>
          <td style="text-align:right">${paymentMethod}</td>
        </tr>
        ${tenderedAmount ? `
        <tr>
          <td>Tendered</td>
          <td style="text-align:right">${formatCurrency(tenderedAmount, currencyCode)}</td>
        </tr>
        <tr>
          <td>Change</td>
          <td style="text-align:right">${formatCurrency(changeAmount || 0, currencyCode)}</td>
        </tr>` : ''}
      </table>
      ${receiptFooter ? `<div class="divider"></div><div class="small center">${receiptFooter}</div>` : ''}
    </body>
    <script>
      window.onload = function() { window.print(); setTimeout(() => window.close(), 500); };
    </script>
  </html>`;

  const w = window.open('', '_blank', 'width=350,height=600');
  if (!w) return;
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  w.location.href = url;
}
