# 🥖 Sistema E-commerce para Panadería Tradicional

Este es un sistema de gestión de ventas y e-commerce desarrollado con **Django**, diseñado específicamente para negocios locales que requieren un control estricto de pedidos, inventario y reportes financieros en tiempo real.

## 🚀 Características Principales

### 🛒 Experiencia del Cliente
* **Catálogo Dinámico:** Gestión de productos (panadería, empanadas, pastelería) controlada desde el panel administrativo.
* **Carrito de Compras:** Sistema fluido para añadir y gestionar productos antes del pago.
* **Logística Inteligente:** Selección entre "Despacho a domicilio" o "Retiro en local" con selector de bloques horarios específicos.
* **Pasarela de Pagos:** Integración con **Mercado Pago** para cobros online y opción de pago presencial.
* **Notificaciones Automáticas:** Envío de correos HTML personalizados al cliente (comprobante) y al vendedor (aviso de preparación).

### ⚙️ Administración y Gestión (Backoffice)
* **Panel Moderno:** Interfaz personalizada utilizando **Jazzmin** para una experiencia de usuario superior.
* **Control de Stock:** Descuento automático de inventario al confirmarse el pago.
* **Gestión de Entregas:** Marcado de pedidos como "Entregados" y filtros por estado de pago.
* **Business Intelligence:** * Reporte visual de ganancias diarias con gráficos de tendencia.
    * Reporte mensual detallado para análisis de crecimiento.
* **Seguridad:** Registro de acciones recientes (audit log) filtrado para seguimiento de órdenes.

## 🛠️ Stack Tecnológico
* **Backend:** Python 3.x / Django 5.x
* **Frontend:** Bootstrap 5, Chart.js (Reportes), JavaScript Vanilla.
* **Base de Datos:** SQLite (Desarrollo) / PostgreSQL (Sugerido para Producción).
* **Integraciones:** Mercado Pago SDK, Django Email MultiAlternatives.

## 📦 Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/lordPobre/Pagina_Panaderia.git](https://github.com/lordPobre/Pagina_Panaderia.git)
   cd Pagina_Panaderia