---
layout: post
title: 'The Ultimate Guide to Generating PDFs from HTML with Node.js and Puppeteer'
description: 'The Ultimate Guide to Generating PDFs from HTML with Node.js and Puppeteer   Posted on:...'
date: 2025-08-21T04:08:00Z
canonical_url: https://dev.to/mofadlalla/the-ultimate-guide-to-generating-pdfs-from-html-with-nodejs-and-puppeteer-2292
---

Ever needed to generate a PDF invoice, a report, or an e-ticket from your web application? It's a common requirement, but turning dynamic HTML into a pixel-perfect PDF can be surprisingly tricky.

In this guide, we'll walk you through the entire process of building a robust PDF generation script using Node.js and Puppeteer, a powerful headless browser tool. We'll cover the basics and also touch on the real-world challenges you might face in a production environment.

## Prerequisites

Before we begin, make sure you have **Node.js** (version 18 or higher) and **npm** installed on your machine.

---

## Step 1: Setting Up Your Project

First, let's create a new project directory and initialize it with a `package.json` file.

```bash
mkdir pdf-generator
cd pdf-generator
npm init -y
```

Next, we need to install Puppeteer. This package will download a recent version of Chromium that we can control programmatically.

```bash
npm install puppeteer
```

## Step 2: The Core PDF Generation Logic

Now for the fun part. Create a file named generate.js and add the following code. This script defines a function that takes a string of HTML, launches a headless browser, and saves the rendered content as a PDF.

```javascript
// generate.js
import puppeteer from 'puppeteer';
import fs from 'fs';

// Example HTML content for an invoice
const invoiceHtml = `
<html>
  <head>
    <style>
      body { font-family: Arial, sans-serif; margin: 40px; }
      .invoice-header { text-align: center; margin-bottom: 40px; }
      .invoice-header h1 { margin: 0; }
      .item-table { width: 100%; border-collapse: collapse; }
      .item-table th, .item-table td { border: 1px solid #ddd; padding: 8px; }
      .item-table th { background-color: #f2f2f2; }
      .total { text-align: right; margin-top: 20px; font-weight: bold; }
    </style>
  </head>
  <body>
    <div class="invoice-header">
      <h1>Invoice #123</h1>
      <p>Issued: August 20, 2025</p>
    </div>
    <table class="item-table">
      <thead>
        <tr><th>Item</th><th>Quantity</th><th>Price</th></tr>
      </thead>
      <tbody>
        <tr><td>Web Development Services</td><td>10</td><td>$150.00</td></tr>
        <tr><td>API Consulting</td><td>5</td><td>$200.00</td></tr>
      </tbody>
    </table>
    <div class="total">
      Total: $2500.00
    </div>
  </body>
</html>
`;

async function generatePdfFromHtml(htmlContent) {
  let browser;
  try {
    console.log('Launching browser...');
    browser = await puppeteer.launch();

    console.log('Opening new page...');
    const page = await browser.newPage();

    console.log('Setting page content...');
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });

    // To ensure all assets like fonts or images are loaded
    await page.emulateMediaType('print');

    console.log('Generating PDF...');
    const pdfBuffer = await page.pdf({
      format: 'A4',
      printBackground: true,
    });

    console.log('Saving PDF...');
    fs.writeFileSync('invoice.pdf', pdfBuffer);

    console.log('PDF generated successfully: invoice.pdf');
  } catch (error) {
    console.error('Error generating PDF:', error);
  } finally {
    if (browser) {
      console.log('Closing browser...');
      await browser.close();
    }
  }
}
generatePdfFromHtml(invoiceHtml);
```

You can run the script from your teminal:

```bash
node generate.js
```

After a few moments, you'll have a beautifully rendered `invoice.pdf` in your project folder!

## Step 3: Optimizing for Performance: From Cold to Warm Starts

Your `generate.js` script is a great starting point, but it has a major performance bottleneck: it launches a new browser instance for every single PDF. This "cold start" can take several seconds and is very inefficient for a real application like a web server.

Let's refactor our code to use a "warm," singleton browser instance that is launched once and reused for all subsequent requests.

First, let's turn our logic into an Express server. If you haven't already, install Express:

```bash
npm install express
```

Now, create an `server.js` file:

```javascript
// server.js
import express from 'express';
import puppeteer from 'puppeteer';

const app = express();
app.use(express.json()); // Middleware to parse JSON bodies

let browser; // We'll hold the browser instance here

// This is an async IIFE (Immediately Invoked Function Expression)
// to launch the browser at the start.
(async () => {
  console.log('Launching a warm browser instance...');
  browser = await puppeteer.launch({
    headless: 'new',
    // Important for running in Docker
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
})();

app.post('/convert', async (req, res) => {
  if (!browser) {
    return res.status(503).send('Browser is not ready.');
  }

  const { html } = req.body;
  if (!html) {
    return res.status(400).send('HTML content is required.');
  }

  const page = await browser.newPage();
  try {
    await page.setContent(html, { waitUntil: 'networkidle0' });
    await page.emulateMediaType('print');

    const pdfBuffer = await page.pdf({
      format: 'A4',
      printBackground: true,
    });

    res.contentType('application/pdf');
    res.send(pdfBuffer);
  } catch (error) {
    console.error('Error generating PDF:', error);
    res.status(500).send('Failed to generate PDF.');
  } finally {
    await page.close(); // IMPORTANT: Only close the page, not the browser
  }
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`PDF generation server listening on port ${PORT}`);
});
```

By moving `puppeteer.launch()` outside the request handler, we've eliminated the cold start. Now, each call to `/convert` is significantly faster.

## Conclusion

Generating PDFs from HTML doesn't have to be a headache. By leveraging Puppeteer, you gain the full power of a modern browser to render your documents exactly as they appear on the web. We've moved from a basic script to a high-performance Express server, setting a solid foundation for any production environment.

From here, you can explore adding custom headers and footers, handling complex CSS layouts, or even integrating this service into a larger microservices architecture. Happy coding!
