# Jegs Bestop Parts Scraper

A comprehensive web scraping solution for extracting Bestop automotive parts data from Jegs.com, including both vehicle application data and detailed product specifications.

## 📋 Overview

This project consists of two main scrapers:

1. **Application Scraper** - Extracts vehicle fitment/application data
2. **Product Details Scraper** - Extracts detailed product specifications and descriptions

Both scrapers are designed to handle large-scale data extraction with robust error handling, CAPTCHA support, and automated Excel report generation.

## 🚀 Features

### Common Features
- **Undetected Chrome Driver** - Bypasses anti-bot detection
- **CAPTCHA Handling** - Manual CAPTCHA solving capability
- **Robust Error Handling** - Comprehensive exception handling and retry logic
- **Excel Export** - Automated formatting with xlwings
- **Logging System** - Detailed logging for debugging and monitoring
- **Resource Cleanup** - Proper driver and temporary file cleanup

### Application Scraper Features
- Vehicle fitment data extraction (Year, Make, Model)
- Part number association with vehicle applications
- Pagination handling for comprehensive data collection
- Vehicle information parsing and categorization

### Product Details Scraper Features
- Complete product specifications extraction
- Product descriptions with bullet points
- Category and title information
- Dynamic column handling for varying specifications
- Structured data organization

## 🛠️ Installation

### Prerequisites
- Python 3.7+
- Chrome browser installed
- Excel (for xlwings functionality)

### Required Packages

```bash
pip install undetected-chromedriver
pip install selenium
pip install seleniumbase
pip install pandas
pip install xlwings
pip install fake-useragent
pip install psutil
```

### Alternative Installation
```bash
pip install -r requirements.txt
```

## 📁 Project Structure

```
jegs-scraper/
├── paste.txt                 # Application scraper script
├── paste-2.txt              # Product details scraper script
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── logs/
    └── jegs_scraper.log     # Scraper logs (auto-generated)
```

## 🔧 Configuration

### Constants (Configurable in both scripts)

```python
WEBSITE = 'https://www.jegs.com/v/Bestop/025?storeId=10001&catalogId=10002&langId=-1&Tab=SKU&csrc=brand'
CAPTCHA_WAIT_TIME = 500      # Time to wait for CAPTCHA solving
ELEMENT_WAIT_TIME = 30       # Maximum wait time for elements
PAGE_LOAD_WAIT_TIME = 30     # Page load timeout
MAX_PAGES = 100              # Maximum pages to scrape (300 for details scraper)
```

## 🚀 Usage

### Running the Application Scraper

```bash
python paste.txt
```

**What it does:**
- Scrapes vehicle application/fitment data
- Extracts Year, Make, Model for each part
- Generates: `Bestop_Application_YYYY-MM-DD.xlsx`

### Running the Product Details Scraper

```bash
python paste-2.txt
```

**What it does:**
- Scrapes detailed product information
- Extracts specifications, descriptions, categories
- Generates: `Bestop_Individual_Part_YYYY-MM-DD.xlsx`

### Interactive Usage

1. **Start the scraper** - Run either script
2. **Handle CAPTCHA** - Manually solve any CAPTCHA challenges when prompted
3. **Monitor Progress** - Watch console output for scraping progress
4. **Retrieve Results** - Find Excel files saved to your Desktop

## 📊 Output Format

### Application Scraper Output
| Part Number | Year | Make | Model | [Additional Fitment Details] |
|-------------|------|------|-------|------------------------------|
| 025-XXX-XXX | 2020 | Ford | F-150 | Engine: 5.0L V8             |

### Product Details Scraper Output
| Part Number | Title | Product Category | Bullet 1 | Bullet 2 | Specs | Description | [Specifications] |
|-------------|-------|------------------|----------|----------|-------|-------------|------------------|
| 025-XXX-XXX | Bestop Soft Top | Convertible Tops | Feature 1 | Feature 2 | | Full description | Brand: Bestop |

## ⚠️ Important Notes

### CAPTCHA Handling
- The scraper will pause when a CAPTCHA is detected
- Manually solve the CAPTCHA in the browser window
- Press Enter in the console to continue

### Rate Limiting
- Built-in delays between requests (1-5 seconds)
- Respectful scraping to avoid overwhelming the server
- Configurable wait times for different operations

### Error Recovery
- Automatic retry logic for stale elements
- Comprehensive exception handling
- Detailed error logging for troubleshooting

## 🔍 Troubleshooting

### Common Issues

**Chrome Driver Issues:**
```bash
# Update Chrome and reinstall undetected-chromedriver
pip uninstall undetected-chromedriver
pip install undetected-chromedriver
```

**Excel Formatting Issues:**
```bash
# Ensure Excel is installed and xlwings is properly configured
pip install --upgrade xlwings
```

**Memory Issues:**
- Reduce `MAX_PAGES` constant
- Monitor system resources during execution
- Ensure sufficient disk space for temporary files

### Debugging

Check the log file for detailed information:
```bash
tail -f jegs_scraper.log
```

Enable verbose logging by modifying the logging level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance

### Typical Performance Metrics
- **Pages per minute:** 5-10 (depending on server response)
- **Parts per hour:** 300-600 (varies by complexity)
- **Memory usage:** 200-500MB peak
- **Network bandwidth:** Moderate (respectful scraping)

### Optimization Tips
- Run during off-peak hours for better performance
- Monitor system resources
- Adjust wait times based on server responsiveness
- Use SSD storage for better temporary file performance

## 🛡️ Best Practices

### Ethical Scraping
- Respect robots.txt guidelines
- Implement reasonable delays between requests
- Monitor server load and adjust accordingly
- Use scraped data responsibly

### Data Management
- Regular backups of scraped data
- Version control for scraper modifications
- Data validation and cleaning procedures
- Proper data storage and organization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with small datasets
4. Submit a pull request with detailed description

## 📄 License

This project is for educational and research purposes. Ensure compliance with target website's terms of service and applicable laws.

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Test with smaller datasets first
4. Ensure all dependencies are properly installed

## 🔄 Version History

- **v1.0** - Initial application scraper
- **v1.1** - Added product details scraper
- **v1.2** - Enhanced error handling and logging
- **v1.3** - Improved Excel formatting and data organization

---

**Note:** This scraper is designed for educational purposes. Always ensure compliance with website terms of service and applicable laws when scraping data.
