import React, { useEffect } from 'react'
import './support.css'
import { FaPhone, FaMapMarkerAlt, FaEnvelope, FaExternalLinkAlt, FaInfoCircle, FaHandsHelping, FaExclamationTriangle, FaHeartbeat } from 'react-icons/fa'

export default function Support() {
  useEffect(() => {
    // Apply color mode from localStorage
    const savedColorMode = localStorage.getItem('colorMode') || 'light'
    if (savedColorMode === 'dark') {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }

    // Apply RG-CVD mode
    const savedRgCvdMode = localStorage.getItem('rgCvdMode') === 'true'
    if (savedRgCvdMode) {
      document.body.classList.add('rg-cvd-mode')
    } else {
      document.body.classList.remove('rg-cvd-mode')
    }
  }, [])

  return (
    <div className="support-page">
      <div className="support-header">
        <h1>支援資源</h1>
        <p className="header-subtitle">香港聽力障礙人士支援組織及資訊</p>
      </div>

      <div className="support-content">
        {/* Main NGOs Section */}
        <section className="support-section">
          <div className="section-title">
            <FaHandsHelping className="section-icon" />
            <h2>主要非政府組織支援</h2>
          </div>

          {/* Hong Kong Society for the Deaf */}
          <div className="org-card">
            <h3>香港聾人福利促進會</h3>
            <p className="org-name-en">Hong Kong Society for the Deaf</p>
            <p className="org-description">
              服務包括：諮詢、家庭支援、青年小組、聽力測試、助聽器服務、緊急支援資訊及家長資源。
            </p>
            
            <div className="contact-info">
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.deaf.org.hk" target="_blank" rel="noopener noreferrer">
                  https://www.deaf.org.hk
                </a>
              </div>
              <div className="contact-item">
                <FaPhone />
                <span>一般查詢：+852 2348 6968</span>
              </div>
              <div className="contact-item">
                <FaMapMarkerAlt />
                <span>總辦事處：香港灣仔軒尼詩道15號溫莎公爵社會服務大廈903室</span>
              </div>
              <div className="contact-item">
                <FaPhone />
                <span>輔導中心（將軍澳）：+852 2711 1974 / WhatsApp 5498 4831</span>
              </div>
            </div>
          </div>

          {/* Hong Kong Association of the Deaf */}
          <div className="org-card">
            <h3>香港聾人協進會 (HKAD)</h3>
            <p className="org-name-en">Hong Kong Association of the Deaf</p>
            <p className="org-description">
              服務包括：權益倡導、社區活動、為聾人及弱聽人士及其家庭提供支援、手語相關工作、捐款資助計劃。
            </p>
            
            <div className="contact-info">
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.hkdeaf.org" target="_blank" rel="noopener noreferrer">
                  https://www.hkdeaf.org
                </a>
              </div>
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.hkdeaf.org/support-us-en/" target="_blank" rel="noopener noreferrer">
                  支持我們（英文頁面）
                </a>
              </div>
            </div>
          </div>

          {/* HISN */}
          <div className="org-card">
            <h3>聽障支援網絡 (HISN)</h3>
            <p className="org-name-en">Hearing Impaired Support Network – Youth Peer Support</p>
            <p className="org-description">
              香港聾人福利促進會轄下的青年網絡。專為主流學校的聾人/弱聽青年（約15-45歲）提供分享、活動及互助支援。
            </p>
            
            <div className="contact-info">
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="http://hisn.deaf.org.hk" target="_blank" rel="noopener noreferrer">
                  http://hisn.deaf.org.hk
                </a>
              </div>
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://hisn.netlify.app/#joinUs" target="_blank" rel="noopener noreferrer">
                  加入我們
                </a>
              </div>
              <div className="contact-item">
                <FaInfoCircle />
                <span>對象：主流學校的聾人/弱聽青年（15-45歲）</span>
              </div>
            </div>
          </div>
        </section>

        {/* Government Services Section */}
        <section className="support-section">
          <div className="section-title">
            <FaInfoCircle className="section-icon" />
            <h2>政府相關服務</h2>
          </div>

          {/* Integrated Service Centre */}
          <div className="org-card">
            <h3>聽障人士綜合服務中心</h3>
            <p className="org-name-en">Social Welfare Department – Integrated Service Centre for Persons with Hearing Impairment</p>
            <p className="org-description">
              政府資助中心，提供：個案工作及輔導、手語傳譯、耳模及技術服務、為聽障人士及其子女（25歲以下）提供聽力及言語治療服務。接受自行轉介。
            </p>
            
            <div className="contact-info">
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.swd.gov.hk/en/pubsvc/rehab/cat_supportcom/centrebase/multiservi/" target="_blank" rel="noopener noreferrer">
                  服務列表及中心詳情
                </a>
              </div>
              <div className="contact-item">
                <FaPhone />
                <span>社會福利署熱線（一般查詢/轉介）：+852 2343 2255</span>
              </div>
            </div>
          </div>

          {/* GovHK */}
          <div className="org-card">
            <h3>香港政府 – 復康及支援服務</h3>
            <p className="org-name-en">GovHK – Rehabilitation & Supports</p>
            <p className="org-description">
              政府復康及殘疾支援服務的一般入口點（包括聽力障礙相關服務）。
            </p>
            
            <div className="contact-info">
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.gov.hk/en/residents/health/rehab/" target="_blank" rel="noopener noreferrer">
                  https://www.gov.hk/en/residents/health/rehab/
                </a>
              </div>
            </div>
          </div>

          {/* Developmental & SEN */}
          <div className="org-card">
            <h3>發展及特殊教育需要資訊（兒童）</h3>
            <p className="org-name-en">Developmental & SEN Information (Children)</p>
            <p className="org-description">
              關於兒童復康及特殊教育需要（SEN）支援（包括聽力障礙）的資訊。
            </p>
            
            <div className="contact-info">
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.dhcas.gov.hk/en/information_rehabilitation.html" target="_blank" rel="noopener noreferrer">
                  DHCAS 復康資訊
                </a>
              </div>
              <div className="contact-item">
                <FaInfoCircle />
                <span>連結至社會福利署及教育局</span>
              </div>
            </div>
          </div>
        </section>

        {/* Emergency Support Section */}
        <section className="support-section emergency-section">
          <div className="section-title">
            <FaExclamationTriangle className="section-icon" />
            <h2>緊急情況及照顧者支援</h2>
          </div>

          {/* 992 Emergency SMS */}
          <div className="org-card emergency-card">
            <h3>992 緊急短訊服務</h3>
            <p className="org-name-en">992 Emergency SMS Service (for Deaf / Speech-impaired)</p>
            <p className="org-description">
              在香港，聽障或語障人士可以在緊急情況下發送短訊至 <strong>992</strong> 聯絡警察/消防/救護服務。
            </p>
            
            <div className="contact-info">
              <div className="contact-item emergency-contact">
                <FaPhone />
                <span className="emergency-number">緊急短訊（香港境內）：992</span>
              </div>
              <div className="contact-item">
                <FaInfoCircle />
                <span>適用於已登記的本地手機號碼用戶 – 請查看最新香港警務處指引</span>
              </div>
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.deaf.org.hk" target="_blank" rel="noopener noreferrer">
                  更多資訊請見「緊急服務」（英文版）
                </a>
              </div>
            </div>
          </div>

          {/* Carer Support Hotline */}
          <div className="org-card">
            <h3>182 183 – 照顧者支援專線</h3>
            <p className="org-name-en">Designated Hotline for Carer Support</p>
            <p className="org-description">
              社會福利署/照顧者支援平台的24小時熱線，包括為聽障人士的照顧者提供建議並轉介至合適服務。
            </p>
            
            <div className="contact-info">
              <div className="contact-item">
                <FaPhone />
                <span>照顧者支援熱線：182 183</span>
              </div>
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.carers.hk" target="_blank" rel="noopener noreferrer">
                  https://www.carers.hk
                </a>
              </div>
            </div>
          </div>
        </section>

        {/* Additional Info Section */}
        <section className="support-section info-section">
          <div className="section-title">
            <FaHeartbeat className="section-icon" />
            <h2>需要協助？</h2>
          </div>
          <div className="info-card">
            <p>
              如果您能告訴我們更多關於您的情況（例如：成人或兒童、新出現的聽力損失或長期問題，以及您目前是否在香港），
              我們可以為您指引<strong>最合適的聯絡方式（非政府組織或政府中心）及首要步驟</strong>。
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
