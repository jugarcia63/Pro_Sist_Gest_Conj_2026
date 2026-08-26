-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 26-08-2026 a las 18:13:52
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `gestion_residencial_db`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `adjuntos_reporte`
--

CREATE TABLE `adjuntos_reporte` (
  `Id_Adjunto` int(11) DEFAULT NULL,
  `Id_Reporte_FK` int(11) DEFAULT NULL,
  `Nombre_Archivo` varchar(150) DEFAULT NULL,
  `Url_Archivo` varchar(255) DEFAULT NULL,
  `Tipo_Archiva` varchar(50) DEFAULT NULL,
  `Fecha_Subida` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos`
--

CREATE TABLE `pagos` (
  `Id_Pago` int(11) DEFAULT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Tipo_Pago` varchar(20) DEFAULT NULL,
  `Id_Reserva_FK` int(11) DEFAULT NULL,
  `Mes_Año` datetime DEFAULT NULL,
  `Valor` decimal(12,2) DEFAULT NULL,
  `Fecha_Vencimiento` date DEFAULT NULL,
  `Fecha_Pago` date DEFAULT NULL,
  `Metodo_Pago` varchar(30) DEFAULT NULL,
  `Comprobante_Url` varchar(255) DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reportes`
--

CREATE TABLE `reportes` (
  `Id_Reportes` int(11) DEFAULT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Categoria` varchar(50) DEFAULT NULL,
  `Descripcion` text DEFAULT NULL,
  `Fecha_Reporte` datetime DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL,
  `Asignado_a_FK` int(11) DEFAULT NULL,
  `Fecha_Resolucion` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reservas`
--

CREATE TABLE `reservas` (
  `Id_Reservas` int(11) DEFAULT NULL,
  `Id_Zona_FK` int(11) DEFAULT NULL,
  `Id_Unidad_FK` int(11) DEFAULT NULL,
  `Fecha_Reserva` datetime DEFAULT NULL,
  `Fecha_Inicio` datetime DEFAULT NULL,
  `Fecha_Fin` datetime DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL,
  `Observaciones` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `residentes`
--

CREATE TABLE `residentes` (
  `Id_Residente` int(11) DEFAULT NULL,
  `Tipo_Documento` varchar(100) DEFAULT NULL,
  `Num_Documento` varchar(100) DEFAULT NULL,
  `Nombres` varchar(255) DEFAULT NULL,
  `Apellidos` varchar(255) DEFAULT NULL,
  `Telefono` varchar(255) DEFAULT NULL,
  `Email` varchar(255) DEFAULT NULL,
  `Id_Unidad_FK` int(11) DEFAULT NULL,
  `Fecha_Registro` datetime DEFAULT NULL,
  `Estado` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles`
--

CREATE TABLE `roles` (
  `Id_Rol` int(11) DEFAULT NULL,
  `Nombre` varchar(100) DEFAULT NULL,
  `Description` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `unidades`
--

CREATE TABLE `unidades` (
  `Id_Unidades` int(11) DEFAULT NULL,
  `Torre` varchar(10) DEFAULT NULL,
  `Apto` varchar(10) DEFAULT NULL,
  `Piso` int(11) DEFAULT NULL,
  `Area` decimal(8,2) DEFAULT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Estado` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `Id_Usuario` int(11) NOT NULL,
  `Nombre` varchar(100) DEFAULT NULL,
  `Email` varchar(100) DEFAULT NULL,
  `Contraseña` varchar(255) DEFAULT NULL,
  `Id_Rol_FK` int(11) DEFAULT NULL,
  `Estado` tinyint(1) DEFAULT NULL,
  `Fecha_creacion` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `vehiculos`
--

CREATE TABLE `vehiculos` (
  `Id_Vehiculos` int(11) DEFAULT NULL,
  `Placa` varchar(10) DEFAULT NULL,
  `Marca` varchar(50) DEFAULT NULL,
  `Modelo` varchar(50) DEFAULT NULL,
  `Color` varchar(30) DEFAULT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Tipo_Vehiculo` varchar(20) DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `visitantes`
--

CREATE TABLE `visitantes` (
  `Id_Visitante` int(11) DEFAULT NULL,
  `Nombre` varchar(100) DEFAULT NULL,
  `Apellidos` varchar(100) DEFAULT NULL,
  `Tipo_Documento` varchar(20) DEFAULT NULL,
  `Num_Documento` varchar(50) DEFAULT NULL,
  `Telefono` varchar(20) DEFAULT NULL,
  `Motivo` varchar(255) DEFAULT NULL,
  `Id_Residente_FK` int(11) DEFAULT NULL,
  `Fecha_Ingreso` datetime DEFAULT NULL,
  `Fecha_Salida` datetime DEFAULT NULL,
  `Autorizado_Por` int(11) DEFAULT NULL,
  `Estado` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `zonas_comunes`
--

CREATE TABLE `zonas_comunes` (
  `Id_Zona` int(11) DEFAULT NULL,
  `Nombre` varchar(100) DEFAULT NULL,
  `Descripcion` varchar(250) DEFAULT NULL,
  `Capacidad` int(11) DEFAULT NULL,
  `Reglas` text DEFAULT NULL,
  `Estado` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
