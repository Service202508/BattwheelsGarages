import React from 'react';
import { Helmet } from 'react-helmet-async';

/**
 * SEO Component for meta tags, OpenGraph, and JSON-LD
 */
const SEO = ({
  title = 'Battwheels Garages | India\'s #1 EV Onsite Service',
  description = 'India\'s first no-towing-first EV service model. Onsite diagnosis and repair for 2W, 3W, 4W and commercial EVs. 85% issues resolved on field.',
  image = '/assets/battwheels-logo-new.png',
  url = '',
  type = 'website',
  article = null,
  noIndex = false,
}) => {
  const siteUrl = process.env.REACT_APP_SITE_URL || 'https://battwheelsgarages.in';
  const fullUrl = url ? `${siteUrl}${url}` : siteUrl;
  const fullImage = image.startsWith('http') ? image : `${siteUrl}${image}`;

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={fullUrl} />
      
      {noIndex && <meta name="robots" content="noindex, nofollow" />}

      {/* OpenGraph Tags */}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={fullImage} />
      <meta property="og:url" content={fullUrl} />
      <meta property="og:type" content={type} />
      <meta property="og:site_name" content="Battwheels Garages" />
      <meta property="og:locale" content="en_IN" />

      {/* Twitter Card Tags */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={fullImage} />

      {/* Article specific tags */}
      {article && (
        <>
          <meta property="article:published_time" content={article.publishedAt} />
          <meta property="article:author" content={article.author} />
          {article.category && <meta property="article:section" content={article.category} />}
        </>
      )}
    </Helmet>
  );
};

export default SEO;
