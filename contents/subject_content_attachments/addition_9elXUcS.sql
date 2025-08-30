
--1. عرض أسماء الوزارات والمشاريع والجهات الممولة، مرتبين حسب أسماء الوزارات تصاعدياً، ثم حسب قيمة التمويل تنازلياً.
SELECT 
    M.Name AS MinistryName,
    P.Name AS ProjectName,
    PH.Name AS PhaseName,
    PH.EstimatedBudget,
    F.Name AS FunderName
FROM Ministry M
JOIN Project P ON M.MinistryID = P.MinistryID
JOIN Phase PH ON P.ProjectID = PH.ProjectID
JOIN ProjectFunding PF ON P.ProjectID = PF.ProjectID
JOIN Funder F ON PF.FunderID = F.FunderID
ORDER BY 
    M.Name DESC,         -- ترتيب أسماء الوزارات تنازليًا
    PH.EstimatedBudget DESC  -- ترتيب القيم التقديرية تنازليًا

         
	------------------------------------------------------------------------------
	--2. عرض أسماء المشاريع التي تم تمويلها من قبل أكثر من جهة ممولة.


SELECT 
    P.Name AS ProjectName
FROM 
    Project P
    JOIN ProjectFunding PF ON P.ProjectID = PF.ProjectID
GROUP BY 
    P.ProjectID, P.Name
HAVING 
    COUNT(DISTINCT PF.FunderID) > 1;

	------------------------------------------------------------------------
--3. عرض أسماء المشاريع التي تتجاوز قيمة موازنتها عشرة مليارات.


SELECT Name
FROM Project
WHERE TotalBudget > 10000000000;
-----------------------------------------------------------------------------


--4عرض التكلفة التقديرية والتكلفة الفعلية لمشاريع وزارة الكهرباء في محافظة حمص، مدينة تدمر. 


SELECT
    p.ProjectID,
    p.Name AS ProjectName,
    SUM(ph.EstimatedBudget) AS TotalEstimatedCost,
    ISNULL(SUM(c.Cost), 0) AS TotalActualCost,
    p.Governorate,
    p.City
FROM Project p
INNER JOIN Ministry m ON p.MinistryID = m.MinistryID
LEFT JOIN Phase ph ON ph.ProjectID = p.ProjectID
LEFT JOIN Contract c ON c.PhaseID = ph.PhaseID
WHERE m.Name = N'وزارة الكهرباء'
  AND p.Governorate = N'حمص'
  AND p.City = N'تدمر'
GROUP BY p.ProjectID, p.Name, p.Governorate, p.City;




