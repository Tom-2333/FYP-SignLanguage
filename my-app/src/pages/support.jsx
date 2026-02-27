import React, { useEffect } from 'react'
import './support.css'
import { FaPhone, FaMapMarkerAlt, FaEnvelope, FaExternalLinkAlt, FaInfoCircle, FaHandsHelping, FaExclamationTriangle, FaHeartbeat } from 'react-icons/fa'
import { useLanguage } from '../contexts/LanguageContext'

export default function Support() {
  const { t } = useLanguage()

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
        <h1>{t('support.title')}</h1>
        <p className="header-subtitle">{t('support.subtitle')}</p>
      </div>

      <div className="support-content">
        {/* Main NGOs Section */}
        <section className="support-section">
          <div className="section-title">
            <FaHandsHelping className="section-icon" />
            <h2>{t('support.mainNgo')}</h2>
          </div>

          {/* Hong Kong Society for the Deaf */}
          <div className="org-card">
            <h3>{t('support.hksd')}</h3>
            <p className="org-name-en">{t('support.hksdEn')}</p>
            <p className="org-description">
              {t('support.hksdDesc')}
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
                <span>{t('support.generalEnquiry')}+852 2348 6968</span>
              </div>
              <div className="contact-item">
                <FaMapMarkerAlt />
                <span>{t('support.headOffice')}</span>
              </div>
              <div className="contact-item">
                <FaPhone />
                <span>{t('support.counsellingCentre')}+852 2711 1974 / WhatsApp 5498 4831</span>
              </div>
            </div>
          </div>

          {/* Hong Kong Association of the Deaf */}
          <div className="org-card">
            <h3>{t('support.hkad')}</h3>
            <p className="org-name-en">{t('support.hkadEn')}</p>
            <p className="org-description">
              {t('support.hkadDesc')}
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
                  {t('support.supportUs')}
                </a>
              </div>
            </div>
          </div>

          {/* HISN */}
          <div className="org-card">
            <h3>{t('support.hisn')}</h3>
            <p className="org-name-en">{t('support.hisnEn')}</p>
            <p className="org-description">
              {t('support.hisnDesc')}
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
                  {t('support.joinUs')}
                </a>
              </div>
              <div className="contact-item">
                <FaInfoCircle />
                <span>{t('support.hisnTarget')}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Government Services Section */}
        <section className="support-section">
          <div className="section-title">
            <FaInfoCircle className="section-icon" />
            <h2>{t('support.govServices')}</h2>
          </div>

          {/* Integrated Service Centre */}
          <div className="org-card">
            <h3>{t('support.isc')}</h3>
            <p className="org-name-en">{t('support.iscEn')}</p>
            <p className="org-description">
              {t('support.iscDesc')}
            </p>

            <div className="contact-info">
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.swd.gov.hk/en/pubsvc/rehab/cat_supportcom/centrebase/multiservi/" target="_blank" rel="noopener noreferrer">
                  {t('support.serviceList')}
                </a>
              </div>
              <div className="contact-item">
                <FaPhone />
                <span>{t('support.swdHotline')}+852 2343 2255</span>
              </div>
            </div>
          </div>

          {/* GovHK */}
          <div className="org-card">
            <h3>{t('support.govhk')}</h3>
            <p className="org-name-en">{t('support.govhkEn')}</p>
            <p className="org-description">
              {t('support.govhkDesc')}
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
            <h3>{t('support.devSen')}</h3>
            <p className="org-name-en">{t('support.devSenEn')}</p>
            <p className="org-description">
              {t('support.devSenDesc')}
            </p>

            <div className="contact-info">
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.dhcas.gov.hk/en/information_rehabilitation.html" target="_blank" rel="noopener noreferrer">
                  {t('support.dhcasInfo')}
                </a>
              </div>
              <div className="contact-item">
                <FaInfoCircle />
                <span>{t('support.linkToSwd')}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Emergency Support Section */}
        <section className="support-section emergency-section">
          <div className="section-title">
            <FaExclamationTriangle className="section-icon" />
            <h2>{t('support.emergency')}</h2>
          </div>

          {/* 992 Emergency SMS */}
          <div className="org-card emergency-card">
            <h3>{t('support.sms992')}</h3>
            <p className="org-name-en">{t('support.sms992En')}</p>
            <p className="org-description">
              {t('support.sms992Desc')}
            </p>

            <div className="contact-info">
              <div className="contact-item emergency-contact">
                <FaPhone />
                <span className="emergency-number">{t('support.emergencySms')}</span>
              </div>
              <div className="contact-item">
                <FaInfoCircle />
                <span>{t('support.sms992Note')}</span>
              </div>
              <div className="contact-item">
                <FaExternalLinkAlt />
                <a href="https://www.deaf.org.hk" target="_blank" rel="noopener noreferrer">
                  {t('support.sms992More')}
                </a>
              </div>
            </div>
          </div>

          {/* Carer Support Hotline */}
          <div className="org-card">
            <h3>{t('support.carerHotline')}</h3>
            <p className="org-name-en">{t('support.carerHotlineEn')}</p>
            <p className="org-description">
              {t('support.carerHotlineDesc')}
            </p>

            <div className="contact-info">
              <div className="contact-item">
                <FaPhone />
                <span>{t('support.carerPhone')}</span>
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
            <h2>{t('support.needHelp')}</h2>
          </div>
          <div className="info-card">
            <p>
              {t('support.needHelpDesc')}
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
