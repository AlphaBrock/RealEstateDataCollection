/* 网页访问参数 */
CREATE TABLE IF NOT EXISTS `ProjectOverviewPageKey`(
	   Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	   ViewState VARCHAR NOT NULL,
	   ViewStateGenerator VARCHAR NOT NULL,
	   EventValidation VARCHAR NOT NULL,
	   `CreateTime` TIMESTAMP NOT NULL DEFAULT (datetime('now','localtime'))
);

/* 单页查询的房产项目信息 */
CREATE TABLE IF NOT EXISTS `ProjectDetailData`(
	   Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	   PresaleDetailsInfoUrl VARCHAR NOT NULL, --项目详情URL
	   PermitNumber VARCHAR NOT NULL, --许可证号
	   DevelopmentEnterprise VARCHAR NOT NULL, --开发企业
	   ProjectName VARCHAR NOT NULL, --项目名称
	   ProjectAddress VARCHAR NOT NULL, --项目地址
	   TimeToMarket TIMESTAMP NOT NULL, --上市时间
	   AreaLocation VARCHAR NOT NULL, --所在区域
	   TotalNumber INTEGER NOT NULL, --总套数
	   AvailableNumber INTEGER NOT NULL, --可售套数
	   PresaleCertificateNumber VARCHAR, --预售证号
	   DateOfCertificate TIMESTAMP, --发证日期
	   CertificateValidFrom TIMESTAMP, --有效期自
	   CertificateExpiryDate TIMESTAMP, --有效期止
	   CertificateAuthority VARCHAR, --发证机关
	   PresaleFundsDepositBank VARCHAR, --预售资金开户银行
	   PresaleFundsSupervisionAccount VARCHAR, --预售资金监管帐号
	   ApprovedPresaleUnits INTEGER, --核准预售套数
	   ApprovedPresaleArea INTEGER, --核准预售面积
	   TotalSoldUnits INTEGER, --已售总套数
	   TotalUnsoldUnits INTEGER, --未售总套数
	   TotalSoldArea INTEGER, --已售总面积
	   TotalUnsoldArea INTEGER, --未售总面积
	   LandCertificateNumber VARCHAR, --土地证号
	   BuildingIds VARCHAR, --楼编号
	   BuildingNames VARCHAR, --楼名称
	   UpdateTime TIMESTAMP NOT NULL DEFAULT (datetime('now','localtime')), --更新时间
	   CreateTime TIMESTAMP NOT NULL DEFAULT (datetime('now','localtime'))
);

/* 每栋楼详细信息 */
CREATE TABLE IF NOT EXISTS `RoomDetailData`(
    Id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    BuildingId VARCHAR, --楼编号
    BuildingName VARCHAR, --楼名称
    RoomNumber VARCHAR, --房号
    RoomInfoUrl VARCHAR, --楼编号
    RoomUse VARCHAR, --房屋用途
    RoomTotalArea REAL, --总面积(平方米)
    RoomInsideArea REAL, --套内面积(平方米)
    RoomSaleStatus VARCHAR, --销售状态
    RoomShareArea REAL, --分摊面积
    RoomFloorNumber INTEGER, --楼层号
    RoomNature VARCHAR, --房屋性质
    RoomType VARCHAR, --户型
    RoomTotalPrice REAL, --房屋申报总价
    RoomUnitPrice REAL, --房屋申报单价
    RoomLocation REAL, --房屋坐落位置
    UpdateTime TIMESTAMP NOT NULL DEFAULT (datetime('now','localtime')), --更新时间
    CreateTime TIMESTAMP NOT NULL DEFAULT (datetime('now','localtime') )
);