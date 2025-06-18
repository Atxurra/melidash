# MercadoLibre Seller Dashboard

   A Django-based web application for MercadoLibre sellers to analyze sales, track inventory, and calculate investment returns by uploading sales reports in Excel format.

   ## Setup Instructions

   ### Prerequisites
   - Python 3.8+
   - Django
   - pandas
   - Git

   ### Installation
   1. **Clone the Repository**
      ```bash
      git clone https://github.com/Atxurra/melidash.git
      cd melidash
      ```

   2. **Create and Activate a Virtual Environment**
      ```bash
      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate
      ```

   3. **Install Dependencies**
      ```bash
      pip install -r requirements.txt
      ```

   4. **Apply Database Migrations**
      ```bash
      python manage.py migrate
      ```

   5. **Create a Superuser**
      To access the Django admin panel and manage data, create a superuser:
      ```bash
      python manage.py createsuperuser
      ```
      Follow the prompts to set a username, email, and password. The superuser allows you to log into the admin panel (`/admin`) to create and modify data.

   6. **Run the Development Server**
      ```bash
      python manage.py runserver
      ```
      Access the app at `http://localhost:8000`.

   ## Key Components
   - **Publications**: Represent products listed on MercadoLibre. Each publication has a unique name and is linked to sales, supplies, and publicity costs. Create publications in the admin panel to organize your data.
   - **Supplies**: Track inventory purchases, including cost, units, purchase date, and arrival date. Add supplies in the admin panel to monitor stock levels.
   - **Stocks**: Implied stock is calculated as total supply units minus total sold units per publication. The dashboard visualizes stock levels and projects future stock based on sales trends.
   - **Sales**: Sales data from MercadoLibre reports, including sale ID, buyer, units sold, income, and costs. Sales are linked to publications for analysis.
   - **Publicity Costs**: Advertising expenses linked to publications, tracked by cost and date.

   ## Uploading New Data
   1. **Download Sales Report**: Log into MercadoLibre, navigate to the sales section, and download the sales report as an Excel (.xlsx) file.
   2. **Access the Upload Page**: Go to the `/excel_upload` endpoint (e.g., `http://localhost:8000/excel_upload`).
   3. **Upload the File**: Select the Excel file and submit. The system will:
      - Parse the file and extract sales data.
      - Match sales to existing publications or flag them as unassigned.
      - Update the database with new or updated sales records.
   4. **Assign Unassigned Publications**: If sales are linked to unrecognized publication names, visit the `/assign_publications` endpoint to assign them to existing publications or create new ones.
   5. **View Analysis**: Go to the `/summary` page to see visualizations of sales trends, stock levels, net investments, and ROI.

   ## Notes
   - Ensure Excel files match the expected MercadoLibre format (header starts at row 6).
   - Use the admin panel (`/admin`) to manually add or edit Publications, Supplies, or Publicity Costs.
   - The SQLite database (`db.sqlite3`) is ignored by Git to prevent sensitive data from being pushed to GitHub.