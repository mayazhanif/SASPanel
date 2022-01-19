-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Jan 19, 2022 at 01:14 AM
-- Server version: 5.7.31
-- PHP Version: 7.3.21

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `saspanel`
--

-- --------------------------------------------------------

--
-- Table structure for table `administrator`
--

DROP TABLE IF EXISTS `administrator`;
CREATE TABLE IF NOT EXISTS `administrator` (
  `Admin_id` int(11) NOT NULL AUTO_INCREMENT,
  `Admin_Name` varchar(100) NOT NULL,
  `Admin_Username` varchar(100) NOT NULL,
  `Admin_Password` varchar(150) NOT NULL,
  `Admin_Email` varchar(150) NOT NULL,
  `Is_Active` int(11) NOT NULL DEFAULT '1',
  `Admin_type` varchar(20) NOT NULL,
  `Reg_Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Admin_id`),
  UNIQUE KEY `Admin_Username` (`Admin_Username`),
  UNIQUE KEY `Admin_Email` (`Admin_Email`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `administrator`
--

INSERT INTO `administrator` (`Admin_id`, `Admin_Name`, `Admin_Username`, `Admin_Password`, `Admin_Email`, `Is_Active`, `Admin_type`, `Reg_Date`) VALUES
(1, 'Test Admin', 'TestAdmin', '123', 'admin@admin.com', 1, '1', '2022-01-17 19:30:07');

-- --------------------------------------------------------

--
-- Table structure for table `domains`
--

DROP TABLE IF EXISTS `domains`;
CREATE TABLE IF NOT EXISTS `domains` (
  `Domain_Id` int(11) NOT NULL,
  `Domain_Name` varchar(200) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Domain_Suspended` int(11) NOT NULL,
  `Is_Deleted` int(11) NOT NULL,
  PRIMARY KEY (`Domain_Id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `ftp_accounts`
--

DROP TABLE IF EXISTS `ftp_accounts`;
CREATE TABLE IF NOT EXISTS `ftp_accounts` (
  `Account_Id` int(11) NOT NULL,
  `Domain_Id` int(11) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Directory` varchar(250) NOT NULL,
  `FTP_Username` varchar(100) NOT NULL,
  `FTP_Password` varchar(200) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`Account_Id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `mail_accounts`
--

DROP TABLE IF EXISTS `mail_accounts`;
CREATE TABLE IF NOT EXISTS `mail_accounts` (
  `Mail_Id` int(11) NOT NULL,
  `Domain_Id` int(11) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Mail_Address` varchar(100) NOT NULL,
  `Mail_Pass` varchar(100) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`Mail_Id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
CREATE TABLE IF NOT EXISTS `notifications` (
  `Notification_ID` int(11) NOT NULL,
  `Admin_id` int(11) NOT NULL,
  `Notification_Title` varchar(50) NOT NULL,
  `Notification_Message` varchar(300) NOT NULL,
  `Notification_Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Is_Active` int(11) NOT NULL,
  `User_id` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `packages`
--

DROP TABLE IF EXISTS `packages`;
CREATE TABLE IF NOT EXISTS `packages` (
  `Package_Id` int(11) NOT NULL AUTO_INCREMENT,
  `Package_Name` varchar(100) NOT NULL,
  `Admin_id` int(11) NOT NULL,
  `Limit_FTP` int(11) NOT NULL,
  `Limit_Mails` int(11) NOT NULL,
  `Limit_Domains` int(11) NOT NULL,
  `CGI_ACCESS` int(11) NOT NULL,
  `Limit_DB` int(11) NOT NULL,
  `Sub_Domains` int(11) NOT NULL,
  `Storage_Limit` int(11) NOT NULL,
  PRIMARY KEY (`Package_Id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `User_id` int(11) NOT NULL AUTO_INCREMENT,
  `User_email` varchar(150) NOT NULL,
  `User_Password` varchar(200) NOT NULL,
  `User_Name` varchar(100) NOT NULL,
  `UserResetToken` varchar(200) NOT NULL,
  `Token_Expiry` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Admin_id` int(11) NOT NULL,
  `Package_id` int(11) NOT NULL,
  `Is_Deleted` int(11) NOT NULL,
  `User_Reg_Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`User_id`),
  UNIQUE KEY `User_email` (`User_email`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`User_id`, `User_email`, `User_Password`, `User_Name`, `UserResetToken`, `Token_Expiry`, `Admin_id`, `Package_id`, `Is_Deleted`, `User_Reg_Date`) VALUES
(1, 'test@test.com', '123', 'Test Account', '', '2022-01-17 19:28:59', 1, 1, 0, '2022-01-17 19:28:59');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
