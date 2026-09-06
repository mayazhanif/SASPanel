-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Apr 12, 2022 at 11:02 AM
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
  `Admin_Password` varchar(512) NOT NULL,
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

-- FIX R10-06: DEFAULT CREDENTIAL REMOVED
-- The original schema shipped with TestAdmin / MD5('123') = 202cb962ac59075b964b07152d234b70
-- This is a trivially guessable password. The installer now creates the admin account interactively.
-- DO NOT insert a default administrator row here.


-- --------------------------------------------------------

--
-- Table structure for table `cronjobs`
--

DROP TABLE IF EXISTS `cronjobs`;
CREATE TABLE IF NOT EXISTS `cronjobs` (
  `Job_ID` int(11) NOT NULL AUTO_INCREMENT,
  `User_id` int(11) NOT NULL,
  `Cron_Command` varchar(200) NOT NULL,
  `Logs_Directory` varchar(200) NOT NULL,
  `Is_Deleted` int(11) NOT NULL,
  PRIMARY KEY (`Job_ID`)
) ENGINE=MyISAM AUTO_INCREMENT=0 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `domains`
--

DROP TABLE IF EXISTS `domains`;
CREATE TABLE IF NOT EXISTS `domains` (
  `Domain_Id` int(11) NOT NULL AUTO_INCREMENT,
  `Domain_Name` varchar(200) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Domain_Suspended` int(11) NOT NULL,
  `Is_Deleted` int(11) NOT NULL,
  PRIMARY KEY (`Domain_Id`),
  UNIQUE KEY `Domain_Name` (`Domain_Name`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `ftp_accounts`
--

DROP TABLE IF EXISTS `ftp_accounts`;
CREATE TABLE IF NOT EXISTS `ftp_accounts` (
  `Account_Id` int(11) NOT NULL AUTO_INCREMENT,
  `User_id` int(11) NOT NULL,
  `Directory` varchar(250) NOT NULL,
  `FTP_Username` varchar(100) NOT NULL,
  `FTP_Password` varchar(512) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`Account_Id`),
  UNIQUE KEY `FTP_Username` (`FTP_Username`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `mail_accounts`
--

DROP TABLE IF EXISTS `mail_accounts`;
CREATE TABLE IF NOT EXISTS `mail_accounts` (
  `Mail_Id` int(11) NOT NULL AUTO_INCREMENT,
  `Domain_Id` int(11) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Mail_Address` varchar(100) NOT NULL,
  `Mail_Pass` varchar(512) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`Mail_Id`),
  UNIQUE KEY `Mail_Address` (`Mail_Address`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `msqldatabases`
--

DROP TABLE IF EXISTS `msqldatabases`;
CREATE TABLE IF NOT EXISTS `msqldatabases` (
  `DB_ID` int(11) NOT NULL AUTO_INCREMENT,
  `DbName` varchar(50) NOT NULL,
  `User_id` int(11) NOT NULL,
  `DbUser_ID` int(11) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`DB_ID`),
  UNIQUE KEY `DbName` (`DbName`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `mysqldbusers`
--

DROP TABLE IF EXISTS `mysqldbusers`;
CREATE TABLE IF NOT EXISTS `mysqldbusers` (
  `DbUser_ID` int(11) NOT NULL AUTO_INCREMENT,
  `DbUsername` varchar(30) NOT NULL,
  `DbPassword` varchar(512) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`DbUser_ID`),
  UNIQUE KEY `DbUsername` (`DbUsername`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

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
  `User_id` int(11) NOT NULL,
  PRIMARY KEY (`Notification_ID`)
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
  `Is_Active` int(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`Package_Id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;

--
-- Dumping data for table `packages`
--

INSERT INTO `packages` (`Package_Id`, `Package_Name`, `Admin_id`, `Limit_FTP`, `Limit_Mails`, `Limit_Domains`, `CGI_ACCESS`, `Limit_DB`, `Sub_Domains`, `Storage_Limit`, `Is_Active`) VALUES
(1, 'Demo_Account', 1, 1, 55, 5, 1, 52, 55, 156, 0),
(2, 'Test', 1, 5, 5, 5, 1, 5, 5, 5, 1),
(3, 'Ultimate', 1, 100, 100, 550, 1, 100, 100, 10, 1);

-- --------------------------------------------------------

--
-- Table structure for table `sslcertificates`
--

DROP TABLE IF EXISTS `sslcertificates`;
CREATE TABLE IF NOT EXISTS `sslcertificates` (
  `Cert_ID` int(11) NOT NULL AUTO_INCREMENT,
  `Domain_Id` int(11) NOT NULL,
  `User_id` int(11) NOT NULL,
  `Certificate` varchar(200) NOT NULL,
  `PrivateKey` varchar(200) NOT NULL,
  `ExpiryDate` date NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`Cert_ID`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `subdomains`
--

DROP TABLE IF EXISTS `subdomains`;
CREATE TABLE IF NOT EXISTS `subdomains` (
  `SDomain_ID` int(11) NOT NULL AUTO_INCREMENT,
  `Domain_Id` int(11) NOT NULL,
  `User_id` int(11) NOT NULL,
  `SubDomain` varchar(100) NOT NULL,
  `Is_Active` int(11) NOT NULL,
  PRIMARY KEY (`SDomain_ID`),
  UNIQUE KEY `SubDomain` (`SubDomain`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `User_id` int(11) NOT NULL AUTO_INCREMENT,
  `servUser` varchar(40) NOT NULL,
  `User_email` varchar(150) NOT NULL,
  `User_Password` varchar(512) NOT NULL,
  `User_Name` varchar(100) NOT NULL,
  `UserResetToken` varchar(200) NOT NULL,
  `Token_Expiry` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Admin_id` int(11) NOT NULL,
  `Package_id` int(11) NOT NULL,
  `Is_Deleted` int(11) NOT NULL,
  `User_Reg_Date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`User_id`),
  UNIQUE KEY `User_email` (`User_email`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
