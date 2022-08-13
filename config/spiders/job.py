from importlib.resources import path
import scrapy


class JobSpider(scrapy.Spider):
    name = 'job'
    allowed_domains = ['karboom.io']
    start_urls = ['https://karboom.io/jobs?q']

    def parse(self, response):
        for page_index in range(1,6):
            url = f'https://karboom.io/jobs?page={page_index}'
            yield scrapy.Request(url = url,callback=self.parse_page)

    def parse_page(self, response):
        jobs = response.xpath('//div[@class="content-column flex-col-between flex-1 overflow-hidden width-75"]')
        # job_urls = response.xpath('//h3[@class="sm-title-size ellipsis-text width-100 m-0"]/a')

        for job in jobs:
            city = job.xpath(".//div/span[@class='pull-right']/text()").get()
            url = job.xpath('.//h3[@class="sm-title-size ellipsis-text width-100 m-0"]/a/@href').get()
            yield scrapy.Request(url = url, callback=self.parse_job,meta={"city" : city})

    def parse_job(self, response):
        city = response.request.meta["city"]
        title = response.xpath("//h1[@class='job-position-title m-t-0']/text()").get()
        url = response.request.url
        
        #image process
        # image_style = response.xpath("//div[@class='employer-branding-image background-cover position-relative']/@style").get()
        # image = image_style.split("(")[1].replace(')','')

        #salary process
        salary = -1
        salary_span = response.xpath('//div[@class="flex-between-center flex-wrap-wrap"]/descendant::span[contains(text(),"تومان")]/text()').get()
        if salary_span :
            if salary_span.__contains__("تا"): salary = salary_span.split("تا")[0]
            else : salary = salary_span


        #job details 
        job_details = response.xpath('//div[@class="jop-position-info active-tab-data"]/div[1]')

        education = None
        education_xpath = job_details.xpath('.//descendant::span[contains(text(),"مقطع تحصیلی")]/following::div[1]/descendant::span/text()').get()

        if education_xpath :
            if education_xpath.__contains__(','): education = education_xpath.split(',')[0].replace('\n', '').replace('،','')
            else : education = education_xpath.replace('\n', '').replace('،','')

        cooperation = None
        cooperation_xpath = job_details.xpath('.//descendant::span[contains(text(),"نوع همکاری")]/following::div[1]/descendant::span/text()').get()
        
        teleworking = False
        if cooperation_xpath :
            if cooperation_xpath.__contains__("دورکاری") : teleworking = True
        
            if cooperation_xpath.__contains__('،'): cooperation = cooperation_xpath.split(',')[0].replace('\n', '').replace(',','')
            else : cooperation = cooperation_xpath.replace('\n', '').replace('،','')
        
        gender = job_details.xpath('.//descendant::span[contains(text(),"جنسیت")]/following::div[1]/descendant::span/text()').get()

        #process for set insurance and experience
        skills = response.xpath('//h3[contains(text(),"الزامات / مهارت‌ها")]/following-sibling::div/text()').get()
        skills_ul = response.xpath('//h3[contains(text(),"الزامات / مهارت‌ها")]/following-sibling::div[@class="md-text-size"]/ul')
        advantages_insurance = response.xpath('//h3[contains(text(),"مزایای شغلی")]/following-sibling::div[@class="md-text-size"]/ul/li[contains(text(),"بیمه")]')

        insurance = False
        experience = -1

        # insurance
        if advantages_insurance : insurance = True
        elif skills_ul :
            li_insurance = skills_ul.xpath('.//li[contains(text(),"بیمه")]')
            if li_insurance : insurance = True
        elif skills :
            for skill in skills: 
                if skill.__contains__('بیمه') : insurance = True
        
        # experience
        if skills_ul :
            li_experience = skills_ul.xpath('.//li[contains(text(),"سال سابقه")]/text()').get()
            if li_experience:
                for m in li_experience:
                    if m.isdigit():
                        experience = m
                        break
        elif skills:
            for skill in skills: 
                if skill.__contains__('سال سابقه') : 
                    for m in skill:
                      if m.isdigit():
                        experience = m
                        break

        yield {
            'title' : title.strip(),
            'city' : city.strip(),
            'education' : education,
            'insurance' : insurance,
            'cooperation' : cooperation,
            'salary' : salary,
            'gender' : gender,
            'experience' : experience,
            'teleworking' : teleworking,
            'url' : url.strip(),
        }    