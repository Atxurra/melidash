# Tablero de Vendedores de MercadoLibre

Una aplicación web basada en Django para vendedores de MercadoLibre que permite analizar ventas, rastrear inventario y calcular retornos de inversión mediante la carga de informes de ventas en formato Excel.

## Instrucciones de Configuración

### Requisitos Previos
- Python 3.8+
- Django
- pandas
- Git

### Instalación
1. **Clonar el Repositorio**
   ```bash
   git clone https://github.com/Atxurra/melidash.git
   cd melidash
   ```

2. **Crear y Activar un Entorno Virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Aplicar Migraciones de la Base de Datos**
   ```bash
   python manage.py migrate
   ```

5. **Crear un Superusuario**
   Para acceder al panel de administración de Django y gestionar datos, crea un superusuario:
   ```bash
   python manage.py createsuperuser
   ```
   Sigue las instrucciones para establecer un nombre de usuario, correo electrónico y contraseña. El superusuario te permite iniciar sesión en el panel de administración (`/admin`) para crear y modificar datos.

6. **Ejecutar el Servidor de Desarrollo**
   ```bash
   python manage.py runserver
   ```
   Accede a la aplicación en `http://localhost:8000`.

## Componentes Clave
- **Publicaciones**: Representan productos listados en MercadoLibre. Cada publicación tiene un nombre único y está vinculada a ventas, suministros y costos de publicidad. Crea publicaciones en el panel de administración para organizar tus datos.
- **Suministros**: Rastrea las compras de inventario, incluyendo costo, unidades, fecha de compra y fecha de llegada. Agrega suministros en el panel de administración para monitorear los niveles de stock.
- **Inventario**: El inventario implícito se calcula como las unidades totales de suministro menos las unidades vendidas por publicación. El tablero visualiza los niveles de stock y proyecta el inventario futuro según las tendencias de ventas.
- **Ventas**: Datos de ventas de los informes de MercadoLibre, incluyendo ID de venta, comprador, unidades vendidas, ingresos y costos. Las ventas están vinculadas a publicaciones para su análisis.
- **Costos de Publicidad**: Gastos de publicidad vinculados a publicaciones, rastreados por costo y fecha.

## Carga de Nuevos Datos
1. **Descargar Informe de Ventas**: Inicia sesión en MercadoLibre, ve a la sección de ventas y descarga el informe de ventas como un archivo Excel (.xlsx).
2. **Acceder a la Página de Carga**: Visita el endpoint `/excel_upload` (por ejemplo, `http://localhost:8000/excel_upload`).
3. **Cargar el Archivo**: Selecciona el archivo Excel y envíalo. El sistema:
   - Analizará el archivo y extraerá los datos de ventas.
   - Vinculará las ventas a publicaciones existentes o las marcará como no asignadas.
   - Actualizará la base de datos con registros de ventas nuevos o actualizados.
4. **Asignar Publicaciones No Asignadas**: Si las ventas están vinculadas a nombres de publicaciones no reconocidos, visita el endpoint `/assign_publications` para asignarlas a publicaciones existentes o crear nuevas.
5. **Ver Análisis**: Ve a la página `/summary` para ver visualizaciones de tendencias de ventas, niveles de stock, inversiones netas y ROI.

## Notas
- Asegúrate de que los archivos Excel coincidan con el formato esperado de MercadoLibre (encabezado comienza en la fila 6).
- Usa el panel de administración (`/admin`) para agregar o editar manualmente Publicaciones, Suministros o Costos de Publicidad.
- La base de datos SQLite (`db.sqlite3`) está ignorada por Git para evitar que se suban datos sensibles a GitHub.